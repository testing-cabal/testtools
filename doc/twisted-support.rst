Twisted support
===============

testtools provides support for running Twisted tests – tests that return a
Deferred_ and rely on the Twisted reactor.

Here's how to use it::

  from testtools import TestCase
  from testtools.deferredruntest import AsynchronousDeferredRunTest

  class MyTwistedTests(TestCase):

      run_tests_with = AsynchronousDeferredRunTest

      def test_foo(self):
          # ...
          return d

Note that you do *not* have to use a special base ``TestCase`` in order to run
Twisted tests, you should just use the regular ``testtools.TestCase`` base
class.

You can also run individual tests within a test case class using the Twisted
test runner::

   class MyTestsSomeOfWhichAreTwisted(TestCase):

       def test_normal(self):
           pass

       @run_test_with(AsynchronousDeferredRunTest)
       def test_twisted(self):
           # ...
           return d


Converting Trial tests to testtools tests
-----------------------------------------

* Use the ``AsynchronousDeferredRunTest`` runner
* Make sure to upcall to ``setUp`` and ``tearDown``
* Don't use ``setUpClass`` or ``tearDownClass``
* Don't expect setting .todo, .timeout or .skip attributes to do anything
* ``flushLoggedErrors`` is ``testtools.deferredruntest.flush_logged_errors``
* ``assertFailure`` is ``testtools.deferredruntest.assert_fails_with``
* Trial spins the reactor a couple of times before cleaning it up,
  ``AsynchronousDeferredRunTest`` does not.  If you rely on this behavior, use
  ``AsynchronousDeferredRunTestForBrokenTwisted``.


.. _Deferred: http://twistedmatrix.com/documents/current/core/howto/defer.html
