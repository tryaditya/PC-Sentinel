# Contributing to PC Sentinel

Thank you for your interest in contributing to PC Sentinel!

We want contributions to be understandable, purposeful, and easy to review. Every contributor must explain **what they changed and why**.

## Before You Start

- Check existing issues and pull requests to avoid duplicate work.
- For major changes, open an issue or discuss the proposal before starting.
- Keep contributions focused. Avoid mixing unrelated changes in one pull request.
- Do not introduce new dependencies without explaining why they are needed.

## Development Setup

1. Fork the repository.
2. Clone your fork.
3. Create and activate a Python virtual environment.
4. Install dependencies using:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Run the application:

   ```bash
   python app.py
   ```

## Pull Request Requirements

Every pull request must include the following information.

### 1. What did you change?

Describe the files, features, bugs, or behavior you modified.

### 2. Why did you make this change?

Explain the problem being solved, the motivation, or the benefit to users.

### 3. How did you test it?

Describe the tests you ran and their results. If you could not test something, say so clearly.

### 4. What could be affected?

Mention any known limitations, compatibility concerns, dependencies, or possible side effects.

### 5. Screenshots or logs

For UI changes, include before-and-after screenshots when useful. For bug fixes, include relevant error messages or test results when appropriate.

## Pull Request Template

Copy and complete this template when submitting a pull request:

**Summary**

What changed?

**Motivation**

Why was this change needed?

**Implementation**

How did you implement it?

**Testing**

What did you test, and what were the results?

**Potential Side Effects**

Could this change affect existing functionality?

**Checklist**

- [ ] I explained what I changed and why.
- [ ] I tested the changes or disclosed what I could not test.
- [ ] I checked that existing functionality still works.
- [ ] I updated documentation where necessary.
- [ ] I disclosed any new dependencies.

## Code Guidelines

- Keep code readable and consistent with the existing project.
- Prefer small, focused changes.
- Avoid unnecessary dependencies.
- Handle errors gracefully.
- Preserve existing functionality unless the change intentionally modifies it.
- Never include passwords, API keys, personal information, or other secrets in commits.

## Review Process

All contributions are subject to maintainer review.

The maintainer may request clarification, additional tests, revisions, or changes before accepting a pull request.

Contributions that do not explain what changed and why may be returned for clarification.

Thank you for helping improve PC Sentinel!
