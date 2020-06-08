Tests
=====
To run tests simply call :code:`pytest`. Many tests are deselected as we need to fix
them due to technical and historical debts. You can find pytest is deselecting
tests marked as :code:`deprecated` and :code:`slow`. Check :code:`pytest.ini` If you want to run
only :code:`deprecated`: :code:`pytest -m deprecated`
