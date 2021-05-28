import brownie
from brownie.test import strategy


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
N = 5


class StateMachine:
    i = strategy("uint256", max_value=N - 1)
    addr = strategy("address", exclude=ZERO_ADDRESS)

    def __init__(cls, accounts, ArrayTest):
        cls.accounts = accounts
        cls.contract = ArrayTest.deploy({"from": accounts[0]})

    def setup(self):
        self.arr = [ZERO_ADDRESS for i in range(N)]
        self.len = 0

    def rule_append(self, addr):
        if self.len == N:
            with brownie.reverts("last not empty"):
                self.contract.append(addr)
        else:
            self.contract.append(addr)
            self.arr[self.len] = addr
            self.len += 1

    def rule_remove(self, i):
        if i >= self.len:
            with brownie.reverts("empty"):
                self.contract.remove(i)
        else:
            self.contract.remove(i)
            del self.arr[i]
            self.arr.append(ZERO_ADDRESS)
            self.len -= 1

    def invariant(self):
        # arrays are equal
        for i in range(N):
            assert self.contract.arr(i) == self.arr[i]

        # check array is packed to left
        z = N  # index of first zero address
        c = 0  # count of non zero addresses
        for i in range(N):
            if self.arr[i] == ZERO_ADDRESS:
                z = i
                break
            else:
                c += 1

        assert self.len == c

        for i in range(N):
            if i < z:
                assert self.arr[i] != ZERO_ADDRESS
            else:
                assert self.arr[i] == ZERO_ADDRESS
        # print(self.arr)
        # print(self.len)


def test_stateful(ArrayTest, accounts, state_machine):
    state_machine(StateMachine, accounts, ArrayTest)