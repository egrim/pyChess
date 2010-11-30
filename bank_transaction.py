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
    balance = account.get_balance()
    with account.lock:
        new_balance = balance + amount
        account.set_balance(new_balance)

if __name__ == '__main__':
    account = BankAccount(1000)
    withdraw_thread = threading.Thread(target=withdraw,
                                       args=(500, account))

    deposit_thread = threading.Thread(target=deposit,
                                      args=(500, account))

    withdraw_thread.start()
    deposit_thread.start()

    withdraw_thread.join()
    deposit_thread.join()

    final_balance = account.get_balance()
    assert final_balance == 1000, "balance mismatch; Expected: %i Found: %i" % (1000, final_balance)
    print "Success!",
