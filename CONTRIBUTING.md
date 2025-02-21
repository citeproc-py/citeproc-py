# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

## Types of Contributions

### Report Bugs

Report bugs at https://github.com/citeproc-py/citeproc-py/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

### Implement Enhancements

Look through the GitHub issues for enhancements. Anything tagged with "enhancement"
is open to whoever wants to implement it.

### Implement Feature Requests

Look through the GitHub issues for feature requests. These are larger projects
 that may take more effort. Anything tagged with "feature request"
is open to whoever wants to implement it.

### Write Documentation

citeproc-py could always use more documentation, whether as part of the
readme, examples, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at
https://github.com/citeproc-py/citeproc-py/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started!

Ready to contribute? Here's how to set up `citeproc-py` for local development.

1. Fork the `citeproc-py` repo on GitHub.
2. Clone your fork locally:

    ```shell
    $ git clone git@github.com:your_name_here/citeproc-py.git
    $ cd citeproc-py
    $ git submodule update --init
    ```

3. Create a branch for local development:

    ```shell
    $ git checkout -b name-of-your-bugfix-or-feature
    ```

   Now you can make your changes locally.

4. When you're done making changes, check that your changes pass tests:

    ```shell
    $ cd tests
    $ python citeproc-test.py
    ```

   This command will list and fixed or newly failing tests. You should
   fix any failures, and commit the ``failing_tests.txt`` file with any
   updates.

5. Commit your changes and push your branch to GitHub:

    ```shell
    $ git add .
    $ git commit -s -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature
    ```

5. Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should not break existing tests. 
2. If you're fixing something or adding a new feature please add test 
   cases so we can see what has been fixed or improved and make sure 
   it doesn't break in the future.

All pull requests need at least one review before they can be merged. 
