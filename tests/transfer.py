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
		SCENARIO("Test notify tranfer action")

		reset()
		create_master_account("master")

		COMMENT("Create test accounts")
		key = CreateKey(is_verbose=False)
		create_account("scrugebounty", master, "scrugebounty", key)
		create_account("provider", master, "provider")
		create_account("hunter", master, "hunter")
		create_account("customtoken1", master, "customtoken1")
		create_account("customtoken2", master, "customtoken2")
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

	def test_project_payment(self):

		# Paying with different token
		with self.assertRaises(Error) as c:
			pay(customtoken1, provider, scrugebounty, "10.0000 KOT", "payment")
		customtoken1.table("accounts", provider)
		self.assertIn("You can only pay for bounty with EOS", c.exception.message)

		# Paying too low
		with self.assertRaises(Error) as c:
			pay(eosio_token, provider, scrugebounty, "0.0001 EOS", "payment")
		self.assertIn("You have to pay 10 EOS", c.exception.message)

		# Paying too much
		with self.assertRaises(Error) as c:
			pay(eosio_token, provider, scrugebounty, "11.0000 EOS", "payment")
		self.assertIn("You have to pay 10 EOS", c.exception.message)

		# Incorrect memo
		with self.assertRaises(Error) as c:
			pay(eosio_token, provider, scrugebounty, "10.0000 EOS", "")
		self.assertIn("This contract only receives tokens to work with bounty. Please, read the description", c.exception.message)

		COMMENT("Paying and creating project")
		pay(eosio_token, provider, scrugebounty, "10.0000 EOS", "payment")

		sleep(1) # work around duplicate transaction

		# Paying twice
		with self.assertRaises(Error) as c:
			pay(eosio_token, provider, scrugebounty, "10.0000 EOS", "payment")
		self.assertIn("You have already paid", c.exception.message)

		# Check table row
		t = scrugebounty.table("payments", scrugebounty)
		self.assertEqual(t.json["rows"][0]["providerName"], "provider")

	def test_pay_submission(self):

		# Trying to pay without a project
		with self.assertRaises(Error) as c:
			pay(customtoken1, provider, scrugebounty, "10.0000 KOT", "0")
		self.assertIn("You don't have a project", c.exception.message)

		# Paying and creating project and bounty
		pay(eosio_token, provider, scrugebounty, "10.0000 EOS", "payment")
		newproject(scrugebounty, provider)
		newbounty(scrugebounty, provider, 1000000000, 10, 2, 0, "1000.0000 TOK", customtoken1)
		submit(scrugebounty, provider, hunter, 0)

		# Submission not a number
		with self.assertRaises(Error) as c:
			pay(customtoken1, provider, scrugebounty, "10.0000 KOT", "abc")
		self.assertIn("Incorrect memo. SubmissionId is a number", c.exception.message)

		# Submission not found
		with self.assertRaises(Error) as c:
			pay(customtoken1, provider, scrugebounty, "10.0000 KOT", "1")
		self.assertIn("Submission not found", c.exception.message)			

		# Paying with different token
		with self.assertRaises(Error) as c:
			pay(customtoken1, provider, scrugebounty, "10.0000 KOT", "0")
		self.assertIn("Trying to pay with a different token", c.exception.message)

		# Paying with different token contract
		with self.assertRaises(Error) as c:
			pay(customtoken2, provider, scrugebounty, "10.0000 TOK", "0")
		self.assertIn("Trying to send tokens from a different contract", c.exception.message)

		COMMENT("Paying with your token")
		pay(customtoken1, provider, scrugebounty, "10.0000 TOK", "0")

		COMMENT("Paying with EOS")
		pay(eosio_token, provider, scrugebounty, "10.0000 EOS", "0")

		sleep(1) # work around duplicate transaction

		# Paying twice with your token
		with self.assertRaises(Error) as c:
			pay(customtoken1, provider, scrugebounty, "10.0000 TOK", "0")
		self.assertIn("Submission has already been paid for with your token", c.exception.message)

		# Paying twice with EOS
		with self.assertRaises(Error) as c:
			pay(eosio_token, provider, scrugebounty, "10.0000 EOS", "0")
		self.assertIn("Submission has already been paid for with EOS", c.exception.message)

		# Check submission paid and paidEOS values
		t = scrugebounty.table("submissions", provider)
		self.assertEqual(t.json["rows"][0]["paid"], "10.0000 TOK")
		self.assertEqual(t.json["rows"][0]["paidEOS"], "10.0000 EOS")

		# Check bounty paid and paidEOS values
		t = scrugebounty.table("bounties", provider)
		self.assertEqual(t.json["rows"][0]["paid"], "10.0000 TOK")
		self.assertEqual(t.json["rows"][0]["paidEOS"], "10.0000 EOS")

		# Check money went to user
		t = customtoken1.table("accounts", hunter)
		self.assertEqual(t.json["rows"][0]["balance"], "10.0000 TOK")
		t = eosio_token.table("accounts", hunter)
		self.assertEqual(t.json["rows"][0]["balance"], "10.0000 EOS")

# main

if __name__ == "__main__":
	unittest.main()