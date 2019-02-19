### Bounty Agreement

# Intent
This contract was written by the Scruge team for the benefit of the EOS community. The purpose of this contract is to create a protocol for creating Bounties on the EOS network.

# Definitions

* _Bounty Agreement:_ This Document  
* _Bounty:_ A useful task presented by a _Provider_ to be completed by _Hunters_ in return for a _Reward_
* _Provider:_ An entity or a person that creates a _Bounty_ and promises a _Reward_ for completing the _Bounty_ 
* _Hunter:_ An entity or a person that accepts from a _Provider_ to complete a  _Bounty_ to receive a _Reward_
* _Reward:_ A collection of cryptocurrencies in the form of _Tokens_ and/or/nor EOS
* _Tokens:_ : a collection of EOS-based tokens. Usually emitted by the _Provider_ as part of the _Project_
* _Project:_ Decentralised application that uses _Tokens_ in its system

# Campaign Creation
_Provider_ that has done this before skips straight to **Bounty Creation**. Otherwise, the _Provider_ does the following steps:

1. _Provider_ sends a fee to the EOS account **scrugebounty**. This fee will only be consumer in the creation of a bounty later.
2. _Provider_ initiates an action **newproject** with a description of their _Project_ specifying:
- Provider Name (name of the account)
- Project Description (including token economies: total supply, inflation rate and expected exchange listing and other relevant info such as whitepaper, links etc.)
- Project Name

In this way, _Provider_ enters into _Bounty Agreement_, gets registered with the **scrugebounty** contracts and receives ID **providerName**

# Bounty Creation

_Provider_ sends a transaction to **scrugebounty** paying a fee for creation of the bounty. Then _Provider_ initiates an action **newbounty** with a description specifying the following:
- Bounty Description
- Rewards Description
- Bounty Duration (in milliseconds)
- Participation Limitations, like:
  * user limit
  * submissions per user
  * time limit for one user to participate again
  * Budget Constraints

In this way, **bountyID** is created.

# Bounty Submission
_Hunter_ accomplished _Bounty_ and sends proof of his work (e.g. a link) via action **submit** to the account **scrugebounty** specifyind **bountyID** and **providerName**. In this way, _Hunter_ enters into _Bounty Agreement_ and **submissionID** is generated.

# Bounty Payout

After a certain period of time (as specified in the _Bounty Description_), a payout is made according to _Rewards_ description. _Provider_ sends a payment to the account **scrugebounty** passing in a memo **submissionID** for which payment is to be made. Payment is automatically sent to the respective _Hunter_

