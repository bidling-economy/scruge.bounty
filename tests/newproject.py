import unittest
from eosfactory.eosf import *
from methods import *
from time import sleep

verbosity([Verbosity.INFO, Verbosity.OUT, Verbosity.TRACE, Verbosity.DEBUG])

CONTRACT_WORKSPACE = "Bounties"

# methods

class Test(unittest.TestCase):

	# setup

	@classmethod
	def tearDownClass(cls):
		stop()

	@classmethod
	def setUpClass(cls):
		SCENARIO("Test newproject action")

		reset()
		create_master_account("master")

		COMMENT("Create test accounts")
		key = CreateKey(is_verbose=False)
		create_account("scrugebounty", master, "scrugebounty", key)
		create_account("provider", master, "provider")
		create_account("hunter", master, "hunter")
		create_account("eosio_token", master, "eosio.token")

		COMMENT("Deploy scrugebounty")
		bounty_contract = Contract(scrugebounty, "scruge.bounty/src")
		if not bounty_contract.is_built():
			bounty_contract.build()
		bounty_contract.deploy()

		COMMENT("Deploy token contracts")
		token_contract = Contract(eosio_token, "02_eosio_token")
		if not token_contract.is_built():
			token_contract.build()
		token_contract.deploy()

		COMMENT("Create and issue tokens")
		create_issue(eosio_token, provider, "EOS")

	def run(self, result=None):
		super().run(result)

	# tests

	def test_create_project(self):

		# Creating a project without paying
		with self.assertRaises(Error) as c:
			newproject(scrugebounty, provider)
		self.assertIn("First pay for bounty creation", c.exception.message)

		COMMENT("Paying and creating project")
		pay(eosio_token, provider, scrugebounty, "10.0000 EOS", "payment")
		newproject(scrugebounty, provider)

		sleep(1) # work around duplicate transaction

		# Check create again
		with self.assertRaises(Error) as c:
			newproject(scrugebounty, provider)
		self.assertIn("You have already created a project", c.exception.message)
		
		# Check payment wasn't consumed
		t = scrugebounty.table("payments", scrugebounty)
		self.assertEqual(t.json["rows"][0]["providerName"], "provider")

		# Check new project values
		t = scrugebounty.table("projects", scrugebounty)
		self.assertEqual(t.json["rows"][0]["providerName"], "provider")

# main

if __name__ == "__main__":
	unittest.main()