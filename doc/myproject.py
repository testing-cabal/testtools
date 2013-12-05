class silly(object):

    @staticmethod
    def square(number):
        try:
            return number ** 2
        except TypeError:
            exception = TypeError("Cannot square '{}', not a number.".format(number))
            exception.bad_value = number
            raise exception
