#include <eosiolib/eosio.hpp>
#include <eosiolib/print.hpp>
#include <eosiolib/asset.hpp>
#include <eosiolib/transaction.hpp>

using namespace eosio;
using namespace std;

// eos 
const symbol& EOS_SYMBOL = symbol {"EOS", 4};

// time
const uint64_t SECOND = 1000;
const uint64_t MINUTE = 60 * SECOND;
const uint64_t HOUR = 60 * MINUTE;
const uint64_t DAY = 24 * HOUR;

// constants
const uint64_t MIN_DURATION_MILLISECONDS = 10 * DAY;
const uint64_t MAX_DURATION_MILLISECONDS = 365 * DAY;

const auto BOUNTY_PRICE = asset(100000, EOS_SYMBOL);
const char* PRICE_ERROR = "You have to pay 10 EOS.";