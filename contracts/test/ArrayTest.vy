# @version 0.2.12

N: constant(uint256) = 5
arr: public(address[N])


@internal
def _pack():
    arr: address[N] = empty(address[N])
    i: uint256 = 0
    for addr in self.arr:
        if addr != ZERO_ADDRESS:
            arr[i] = addr
            i += 1
    self.arr = arr


@external
def append(addr: address):
    assert self.arr[N - 1] == ZERO_ADDRESS, "last not empty"
    self.arr[N - 1] = addr
    self._pack()


@external
def remove(i: uint256):
    assert i < N, "i >= N"
    assert self.arr[i] != ZERO_ADDRESS, "empty"
    self.arr[i] = ZERO_ADDRESS
    self._pack()


@external
@view
def find(addr: address) -> uint256:
    for i in range(N):
        if self.arr[i] == addr:
            return i
    raise "not found"
