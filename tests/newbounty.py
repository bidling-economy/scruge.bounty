import unittest
from eosfactory.eosf import *
from methods import *
from time import sleep

verbosity([Verbosity.INFO, Verbosity.OUT, Verbosity.TRACE, Verbosity.DEBUG])

CONTRACT_WORKSPACE = "scruge.bounty"

# methods

class Test(unittest.TestCase):

	# setup

	@classmethod
	def tearDownClass(cls):
		stop()

	@classmethod
	def setUpClass(cls):
		SCENARIO("Test newbounty action")

		reset()
		create_master_account("master")

		COMMENT("Create test accounts")
		key = CreateKey(is_verbose=False)
		create_account("scrugebounty", master, "scrugebounty", key)
		create_account("provider", master, "provider")
		create_account("hunter", master, "hunter")
		create_account("customtoken1", master, "customtoken1")
		create_account("customtoken2", master, "customtoken2")
		create_account("justaccount", master, "justaccount")
		create_account("eosio_token", master, "eosio.token")

		scrugebounty.set_account_permission(
			Permission.ACTIVE, 
			{
					"threshold" : 1,
					"keys" : [{ "key": key.key_public, "weight": 1 }],
					"accounts": [{
						"permission": {
							"actor": "scrugebounty",
							"permission": "eosio.code"
						},
						"weight": 1
					}],
				},
			Permission.OWNER, (scrugebounty, Permission.OWNER))

		COMMENT("Deploy scrugebounty")
		bounty_contract = Contract(scrugebounty, "scruge.bounty/src")
		if not bounty_contract.is_built():
			bounty_contract.build()
		bounty_contract.deploy()

		COMMENT("Deploy token contracts")
		token_contract = Contract(customtoken1, "02_eosio_token")
		if not token_contract.is_built():
			token_contract.build()
		token_contract.deploy()

		eosio_token_contract = Contract(eosio_token, "02_eosio_token")
		if not eosio_token_contract.is_built():
			eosio_token_contract.build()
		eosio_token_contract.deploy()

		eosio_token_contract = Contract(customtoken2, "02_eosio_token")
		if not eosio_token_contract.is_built():
			eosio_token_contract.build()
		eosio_token_contract.deploy()

		COMMENT("Create and issue tokens")
		create_issue(eosio_token, provider, "EOS")
		create_issue(customtoken1, provider, "TOK")
		create_issue(customtoken1, provider, "KOT")
		create_issue(customtoken2, provider, "TOK")

	def run(self, result=None):
		super().run(result)

	# tests

	def test_newbounty(self):
		SECOND = 1000;
		MINUTE = 60 * SECOND
		HOUR = 60 * MINUTE
		DAY = 24 * HOUR
		duration = 15 * DAY

		# Token account doesn't exist
		with self.assertRaises(Error) as c: # submissionLimit, limitPerUser, resubmissionPeriodMilliseconds
			newbounty(scrugebounty, provider, duration, 10, 2, 0, "1000.0000 TOK", "nonexistant")
		self.assertIn("Token contract account does not exist", c.exception.message)

		# No tokens were issued or transferred to user
		with self.assertRaises(Error) as c:
			newbounty(scrugebounty, provider, duration, 10, 2, 0, "1000.0000 TOK", justaccount)
		self.assertIn("You don't have any of these tokens", c.exception.message)
		
		# Token precision mismatch with actual contract
		with self.assertRaises(Error) as c:
			newbounty(scrugebounty, provider, duration, 10, 2, 0, "1000.000 TOK", customtoken1)
		self.assertIn("Budget symbol precision mismatch", c.exception.message)

		# Did not pay
		with self.assertRaises(Error) as c:
			newbounty(scrugebounty, provider, duration, 10, 2, 0, "1000.0000 TOK", customtoken1)
		self.assertIn("You did not pay for bounty creation yet", c.exception.message)

		COMMENT("Creating project")
		pay(eosio_token, provider, scrugebounty, "10.0000 EOS", "payment")
		newproject(scrugebounty, provider)

		# Short duration
		with self.assertRaises(Error) as c:
			newbounty(scrugebounty, provider, 5 * DAY, 10, 2, 0, "1000.0000 TOK", customtoken1)
		self.assertIn("Bounty can not be this short", c.exception.message)

		# Long duration
		with self.assertRaises(Error) as c:
			newbounty(scrugebounty, provider, 1000 * DAY, 10, 2, 0, "1000.0000 TOK", customtoken1)
		self.assertIn("Bounty can not be this long", c.exception.message)

		COMMENT("Creating bounty")
		newbounty(scrugebounty, provider, duration, 10, 2, 0, "1000.0000 TOK", customtoken1)

		# Check bounty created
		t = scrugebounty.table("bounties", provider)
		self.assertEqual(t.json["rows"][0]["paid"], "0.0000 TOK")
		self.assertEqual(t.json["rows"][0]["paidEOS"], "0.0000 EOS")
		self.assertEqual(t.json["rows"][0]["submissions"], 0)
		self.assertEqual(t.json["rows"][0]["participantsPaid"], 0)
		self.assertEqual(t.json["rows"][0]["providerName"], "provider")
		self.assertTrue(int(t.json["rows"][0]["endTimestamp"]) > duration)

# main

if __name__ == "__main__":
	unittest.main()