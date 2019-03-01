#include "const.hpp"

bool is_number(const string& s) {
    return !s.empty() && s.find_first_not_of("0123456789") == string::npos;
}

uint64_t time_ms() {
  return current_time() / 1000;
}

class [[eosio::contract]] scrugebounty : public contract {
  
  public:
    using contract::contract;
    
    scrugebounty(name receiver, name code, datastream<const char*> ds)
        :contract(receiver, code, ds) {}

    ACTION newproject(name providerName, string projectDescription, string projectName);
  
    ACTION newbounty(name providerName, string bountyName, string bountyDescription, string rewardsDescription, 
        string rulesDescription, uint64_t durationMilliseconds, uint64_t submissionLimit, 
        uint64_t limitPerUser, uint64_t resubmissionPeriodMilliseconds, asset budget, name tokenContract);
    
    ACTION submit(name hunterName, name providerName, string proof, uint64_t bountyId);
  
    ACTION notifybounty(uint64_t submissionId, string proof, name providerName, uint64_t bountyId);
      
    void transfer(name from, name to, asset quantity, string memo);
  
  private:
  
    void _transfer(name contract, name from, name to, asset quantity, string memo) {
    	action(
    		permission_level{ from, "active"_n },
        contract, "transfer"_n,
    		make_tuple(from, to, quantity, memo)
    	).send();
    }
    
  	struct [[eosio::table]] bounties {
  		uint64_t bountyId;
  		name providerName;
  		string bountyDescription;
  		string rewardsDescription;
  		string rulesDescription;
  		string bountyName;
  		name tokenContract;
  		
  		uint64_t submissionLimit;
  		uint64_t limitPerUser;
  		uint64_t resubmissionPeriodMilliseconds;
  		uint64_t endTimestamp;
  		asset budget;
  		
  		asset paid;
  		asset paidEOS;
  		uint64_t timestamp;
  		uint64_t submissions;
  		uint64_t participantsPaid;
  
  		uint64_t primary_key() const { return bountyId; }
  	};
  	
  	typedef multi_index<"bounties"_n, bounties> bounties_i;
  	
  	struct [[eosio::table]] submissions {
  	  uint64_t submissionId;
  		uint64_t timestamp;
  	  name hunterName;
  	  name providerName;
      string proof;
      uint64_t bountyId;
      asset paid;
      asset paidEOS;
      
      uint64_t primary_key() const { return submissionId; }
  	};
  	
  	typedef multi_index<"submissions"_n, submissions> submissions_i;
  	
  	 struct [[eosio::table]] payments {
  	   name providerName;
  	   
  	   uint64_t primary_key() const { return providerName.value; }
  	 };
  	
  	typedef multi_index<"payments"_n, payments> payments_i;
  	
  	 struct [[eosio::table]] projects {
  	  name providerName;
  	  string projectDescription;
  	  string projectName;
  	   
  	   uint64_t primary_key() const { return providerName.value; }
  	 };
  	
  	typedef multi_index<"projects"_n, projects> projects_i;
  	
    // token accounts
    struct st_account {
      asset balance; 
      uint64_t primary_key() const { return balance.symbol.code().raw(); }
    };
    
    typedef eosio::multi_index< "accounts"_n, st_account > st_accounts_i;
};