import threading

BALANCE_START = 10000

AMOUNT_WITHDRAW = 5000
AMOUNT_DEPOSIT = 5000

BALANCE_EXPECTED = BALANCE_START - AMOUNT_WITHDRAW + AMOUNT_DEPOSIT

class BankAccount(object):
    def __init__(self, initial_balance=0):
        self.lock = threading.Lock()

        self._balance = initial_balance

    def get_balance(self):
        return self._balance

    def set_balance(self, balance):
        self._balance = balance


def withdraw(amount, account):
    with account.lock:
        balance = account.get_balance()
        new_balance = balance - amount
        account.set_balance(new_balance)

def deposit(amount, account):
    with account.lock:
        balance = account.get_balance()
        new_balance = balance + amount
        account.set_balance(new_balance)

if __name__ == '__main__':
    account = BankAccount(BALANCE_START)
    withdraw_thread = threading.Thread(target=withdraw,
                                       args=(AMOUNT_WITHDRAW, account))

    deposit_thread = threading.Thread(target=deposit,
                                      args=(AMOUNT_DEPOSIT, account))

    withdraw_thread.start()
    deposit_thread.start()

    withdraw_thread.join()
    deposit_thread.join()

    final_balance = account.get_balance()
    assert final_balance == BALANCE_EXPECTED, "balance mismatch; Expected: %i Found: %i" % (BALANCE_EXPECTED, final_balance)
    print "Success!",
#    if final_balance != BALANCE_EXPECTED:
#        print "Error - balance mismatch; Expected: %i Found: %i" % (BALANCE_EXPECTED, final_balance)
#    else:
#        print "Success!"
