class silly(object):

    @staticmethod
    def square(number):
        try:
            return number ** 2
        except TypeError:
            exception = TypeError("Cannot square '{0}', not a number.".format(number))
            exception.bad_value = number
            raise exception


square = silly.square

def is_prime(n):
    '''check if integer n is a prime'''
    # make sure n is a positive integer
    n = abs(int(n))
    # 0 and 1 are not primes
    if n < 2:
        return False
    # 2 is the only even prime number
    if n == 2:
        return True
    # all other even numbers are not primes
    if not n & 1:
        return False
    # range starts with 3 and only needs to go up the squareroot of n
    # for all odd numbers
    for x in range(3, int(n**0.5)+1, 2):
        if n % x == 0:
            return False
    return True


def divisible(a, b):
    return a % b == 0


class Person(object):

    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    @property
    def full_name(self):
        return '{0} {1}'.format(self.first_name, self.last_name)


class SomeServer(object):

    logfile = 'greetings.txt'
    temperature = 'cool'

    def start_up(self):
        pass

    def shut_down(self):
        pass


class Server(object):

    def getDetails(self):
        return {}

    def setUp(self):
        pass

    def cleanUp(self):
        pass
