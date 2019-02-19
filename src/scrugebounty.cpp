#include "scrugebounty.hpp"

void scrugebounty::newproject(name providerName, string projectDescription, string projectName) {
  require_auth(providerName);
  
  eosio_assert(projectName != "", "Enter your project name.");
  eosio_assert(projectDescription != "", "Enter your project description.");
  
  projects_i projects(_self, _self.value);
  auto project = projects.find(providerName.value);
  eosio_assert(project == projects.end(), "You have already created a project.");
  
  payments_i payments(_self, _self.value);
  auto payment = payments.find(providerName.value);
  eosio_assert(payment != payments.end(), "First pay for bounty creation.");
  
  projects.emplace(providerName, [&](auto& r) {
    r.providerName = providerName;
    r.projectName = projectName;
    r.projectDescription = projectDescription;
  });
}

void scrugebounty::newbounty(name providerName, string bountyName, string bountyDescription, string rewardsDescription, 
    string rulesDescription, uint64_t durationMilliseconds, uint64_t userLimit, 
    uint64_t limitPerUser, uint64_t timeLimit, asset budget, name tokenContract) {
  
  require_auth(providerName);
  eosio_assert(is_account(tokenContract), "Token contract account does not exist.");
  
  st_accounts_i st_accounts(tokenContract, providerName.value);
  auto account = st_accounts.find(budget.symbol.code().raw());
  eosio_assert(account != st_accounts.end(), "You don't have any of these tokens.");
  eosio_assert(account->balance.symbol == budget.symbol,"Budget symbol precision mismatch.");
  
  payments_i payments(_self, _self.value);
  auto payment = payments.find(providerName.value);
  eosio_assert(payment != payments.end(), "You did not pay for bounty creation yet.");
  
  eosio_assert(bountyDescription != "", "Enter your bounty description.");
  eosio_assert(rewardsDescription != "", "Enter your rewards description.");
  eosio_assert(bountyName != "", "Enter your bounty name.");
  eosio_assert(bountyName.length() < 50, "Bounty name should be shorter than this.");
  
  eosio_assert(durationMilliseconds > MIN_DURATION_MILLISECONDS,
      "Bounty can not be this short.");
      
  eosio_assert(durationMilliseconds < MAX_DURATION_MILLISECONDS, 
      "Bounty can not be this long.");
  
  bounties_i bounties(_self, providerName.value);
  auto bountyId = bounties.available_primary_key();
  
  bounties.emplace(providerName, [&](auto& r) {
    r.bountyId = bountyId;
    r.providerName = providerName;
    r.bountyDescription = bountyDescription;
    r.rewardsDescription = rewardsDescription;
    r.bountyName = bountyName;
    r.rulesDescription = rulesDescription;
    r.tokenContract = tokenContract;
    r.timestamp = time_ms();
    
    r.limitPerUser = limitPerUser;
    r.timeLimit = timeLimit;
    r.userLimit = userLimit;
    r.endTimestamp = time_ms() + durationMilliseconds;
    r.budget = budget;
    
    r.timeLimit = timeLimit;
    r.paid = asset(0, budget.symbol);
    r.paidEOS = asset(0, EOS_SYMBOL);
    r.participantsPaid = 0;
    r.submissions = 0;
  });
  
  payments.erase(payment);
}

void scrugebounty::submit(name hunterName, name providerName, string proof, uint64_t bountyId) {
  require_auth(hunterName);
  
  eosio_assert(proof != "", "Enter your proof of work. This can be url or any other text.");
  
  projects_i projects(_self, _self.value);
  auto project = projects.find(providerName.value);
  eosio_assert(project != projects.end(), "This project doesn't exist.");
  
  bounties_i bounties(_self, providerName.value);
  auto bounty = bounties.find(bountyId);
  eosio_assert(bounty != bounties.end(), "This bounty doesn't exist.");
  
  auto limitPerUser = bounty->limitPerUser;
  auto timeLimit = bounty->timeLimit;
  auto userLimit = bounty->userLimit;
  auto budget = bounty->budget;
  auto paid = bounty->paid;
  auto endTimestamp = bounty->endTimestamp;
  
  submissions_i submissions(_self, providerName.value);
  
  eosio_assert(time_ms() < endTimestamp, "This bounty has ended.");
  
  // check limits 
  auto submissionsCount = 0;
  auto userSubmissionsCount = 0;
  uint64_t latestUserSubmissionTime = 0;
  
  for (auto& submission: submissions) {
    
    if (submission.bountyId == bountyId) {
      submissionsCount++;
      
      if (submission.hunterName == hunterName) {
        userSubmissionsCount++;

        if (submission.timestamp > latestUserSubmissionTime) {
          latestUserSubmissionTime = submission.timestamp;
        }
      }
    }
  }
  
  auto resubmissionPeriod = time_ms() - latestUserSubmissionTime;
  
  eosio_assert(budget.amount > paid.amount,
      "This bounty has reached its budget limit.");
  
  eosio_assert(limitPerUser == 0 || userSubmissionsCount < limitPerUser,
      "You have reached per user limit of submissions.");
      
  eosio_assert(timeLimit == 0 || resubmissionPeriod > timeLimit,
      "You can not submit for this bounty this soon again.");
      
  eosio_assert(userLimit == 0 || submissionsCount < userLimit,
      "This bounty has reached submissions limit.");
      
  
  auto submissionId = submissions.available_primary_key();
  
  bounties.modify(bounty, providerName, [&](auto& r) {
    r.submissions++;
  });
  
  submissions.emplace(hunterName, [&](auto& r) {
    r.submissionId = submissionId;
    r.providerName = providerName;
    r.hunterName = hunterName;
    r.proof = proof;
    r.bountyId = bountyId;
    r.paid = asset(0, bounty->budget.symbol);
    r.paidEOS = asset(0, EOS_SYMBOL);
    r.timestamp = time_ms();
  });
  
  // notify about submission
  transaction t{};
  t.actions.emplace_back(permission_level(_self, "active"_n), 
                        _self, "notifybounty"_n, 
          					    make_tuple(submissionId, proof, providerName, bountyId));
  t.delay_sec = 1;
  t.send(time_ms(), _self, true);
}

void scrugebounty::notifybounty(uint64_t submissionId, string proof, name providerName, uint64_t bountyId) {
  require_auth(_self);
  require_recipient(providerName);
}

void scrugebounty::transfer(name from, name to, asset quantity, string memo) {
  require_auth(from);
  if (to != _self || from == _self) { return; }
  
	eosio_assert(quantity.symbol.is_valid(), "Invalid quantity.");
	eosio_assert(quantity.amount > 0, "Only positive quantity allowed.");
	eosio_assert(memo != "", 
	    "This contract only receives tokens to work with bounty. Please, read the description.");
  
  auto code = name(get_code());
  
  if (memo == "payment") {
    eosio_assert(code == "eosio.token"_n, "You can only pay for bounty with EOS.");
    eosio_assert(quantity.amount == BOUNTY_PRICE.amount 
                && quantity.symbol == BOUNTY_PRICE.symbol, PRICE_ERROR);
    
    payments_i payments(_self, _self.value);
    auto payment = payments.find(from.value);
    eosio_assert(payment == payments.end(), "You have already paid.");
    
    payments.emplace(_self, [&](auto& r) {
      r.providerName = from;
    });
  }
  else {
    projects_i projects(_self, _self.value);
    auto project = projects.find(from.value);
    eosio_assert(project != projects.end(), "You don't have a project.");
    auto providerName = project->providerName;
    
    eosio_assert(is_number(memo), "Incorrect memo. SubmissionId is a number.");
    auto submissionId = stoull(memo);
    
    submissions_i submissions(_self, providerName.value);
    auto submission = submissions.find(submissionId);
    eosio_assert(submission != submissions.end(), "Submission not found.");
    
    bounties_i bounties(_self, providerName.value);
    auto bounty = bounties.find(submission->bountyId);
    auto hunterName = name(submission->hunterName);
    
    bool isPayingEOS = code == "eosio.token"_n;
    bool previouslyPaid = 
        submission->paid.amount != 0 || submission->paidEOS.amount != 0;
    
    if (code == "eosio.token"_n) {
      eosio_assert(quantity.symbol == EOS_SYMBOL,
          "You can only use EOS on eosio.token contract.");
      eosio_assert(submission->paidEOS.amount == 0,
          "Submission has already been paid for with EOS.");
    }
    else {
      eosio_assert(bounty->tokenContract == code,
          "Trying to send tokens from a different contract.");
      eosio_assert(bounty->paid.symbol == quantity.symbol, 
          "Trying to pay with a different token.");
      eosio_assert(submission->paid.amount == 0, 
          "Submission has already been paid for with your token.");
    }

    submissions.modify(submission, hunterName, [&](auto& r) {
      if (isPayingEOS) {
        r.paidEOS += quantity;
      }
      else {
        r.paid += quantity;
      }
    });
    
    bounties.modify(bounty, providerName, [&](auto& r) {
      if (isPayingEOS) {
        r.paidEOS += quantity;
      }
      else {
        r.paid += quantity;
      }
      
      if (!previouslyPaid) {
        r.participantsPaid++;
      }
    });
    
    _transfer(code, _self, hunterName, quantity, "BIDLing Economy: Scruge Bounty Reward.");
  }
}

extern "C" {
  
  void apply(uint64_t receiver, uint64_t code, uint64_t action) {
    
    if (code == receiver) {
  	  switch (action) {
        EOSIO_DISPATCH_HELPER(scrugebounty, 
            (newproject)(newbounty)(submit)(notifybounty))
  	  }
    }
  	else if (action == "transfer"_n.value && code != receiver) {
  	  execute_action(name(receiver), name(code), &scrugebounty::transfer);
  	}
  }
};
