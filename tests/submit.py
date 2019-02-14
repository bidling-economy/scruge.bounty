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
		SCENARIO("Test submit action")

		reset()
		create_master_account("master")

		COMMENT("Create test accounts")
		key = CreateKey(is_verbose=False)
		create_account("scrugebounty", master, "scrugebounty", key)
		create_account("provider", master, "provider")
		create_account("hunter", master, "hunter")
		create_account("customtoken1", master, "customtoken1")
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

		COMMENT("Create and issue tokens")
		create_issue(eosio_token, provider, "EOS")
		create_issue(customtoken1, provider, "TOK")

	def run(self, result=None):
		super().run(result)

	# tests

	def test_newbounty(self):
		DAY = 24 * 60 * 60 * 1000
		duration = 15 * DAY

		# Project doesn't exist
		with self.assertRaises(Error) as c:
			submit(scrugebounty, provider, provider, 0)
		self.assertIn("This project doesn't exist", c.exception.message)

		COMMENT("Creating project")
		pay(eosio_token, provider, scrugebounty, "10.0000 EOS", "payment")
		newproject(scrugebounty, provider)

		# Bounty doesn't exist
		with self.assertRaises(Error) as c:
			submit(scrugebounty, provider, provider, 0)
		self.assertIn("This bounty doesn't exist", c.exception.message)

		COMMENT("Creating bounty")
		newbounty(scrugebounty, provider, duration, 0, 0, 0, "1000.0000 TOK", customtoken1)

		COMMENT("Creating submission")
		submit(scrugebounty, provider, hunter, 0)

		# Check bounty created
		t = scrugebounty.table("submissions", provider)
		self.assertEqual(t.json["rows"][0]["paid"], "0.0000 TOK")
		self.assertEqual(t.json["rows"][0]["paidEOS"], "0.0000 EOS")
		self.assertEqual(t.json["rows"][0]["bountyId"], 0)
		self.assertEqual(t.json["rows"][0]["hunterName"], "hunter")
		self.assertEqual(t.json["rows"][0]["providerName"], "provider")

# main

if __name__ == "__main__":
	unittest.main()