import unittest
from eosfactory.eosf import *

# methods

def pay(contract, fromAccount, to, quantity, memo):
	contract.push_action("transfer",
		{
			"from": fromAccount,
			"to": to,
			"quantity": quantity,
			"memo": memo
		},
		permission=[(fromAccount, Permission.ACTIVE)])

def newproject(scrugebounty, provider):
	scrugebounty.push_action("newproject",
		{
			"providerName": provider,
			"projectDescription": "Test project",
			"projectName": "Project 1"
		},
		permission=[(provider, Permission.ACTIVE)])

def newbounty(scrugebounty, provider, duration, userLimit, limitPerUser, timeLimit, budget, tokenContract):
	scrugebounty.push_action("newbounty",
		{
			"providerName":  provider,
			"bountyDescription":  "Bounty Description",
			"rewardsDescription":  "Reward Description",
			"rulesDescription": "Rules Description",
    		"durationMilliseconds":  duration,
    		"userLimit":  userLimit,
    		"limitPerUser":  limitPerUser,
    		"timeLimit":  timeLimit,
    		"budget":  budget,
    		"tokenContract": tokenContract
		}, 
		permission=[(provider, Permission.ACTIVE)])

def submit(scrugebounty, provider, hunter, bountyId):
	scrugebounty.push_action("submit",
		{
			"hunterName": hunter, 
			"providerName": provider,
			"proof": "I did it",
			"bountyId": bountyId
		},
		permission=[(hunter, Permission.ACTIVE)])

def create_issue(contract, to, symbol):
	contract.push_action("create",
		{
			"issuer": to,
			"maximum_supply": "1000.0000 {}".format(symbol)
		},
		permission=[(contract, Permission.ACTIVE)])
	contract.push_action("issue",
		{
			"to": to,
			"quantity": "1000.0000 {}".format(symbol),
			"memo": ""
		},
		permission=[(to, Permission.ACTIVE)])