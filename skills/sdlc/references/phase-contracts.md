# Phase Contracts

## Common handoff

Every phase reports its artifact paths, verification performed, deviations, open questions, and a clear pass/fail verdict. Agents must not advance the workflow themselves.

## Product

Input: user request and repository context. Output: PRD with goals, user stories, testable acceptance criteria, rules, scope, out-of-scope, metrics, and open questions. Completion: core behavior is unambiguous enough to design.

## Architecture

Input: approved PRD and codebase. Output: architecture with stack, data/API contracts, flows, infrastructure, security, and open questions. Completion: developer and QA do not need to invent contracts.

## UI

Input: approved PRD/architecture and existing design system. Output: components, states, copy, responsive behavior, accessibility, and styling tokens. Completion: rendered behavior is testable.

## QA pre-code

Input: approved specs. Output: acceptance-criteria matrix, failing automated tests, exclusions, and evidence that test syntax is valid. Completion: implementation has an executable contract.

## Development

Input: approved specs/tests. Output: production code, passing tests/lint/build, commits when authorized, and deviations. Completion: all approved criteria are implemented.

## QA and UI QA

Input: implementation and criteria. Output: evidence per criterion and pass/fail report. Completion: no blocker remains. Verification agents report defects; they do not silently repair production code.

## Code review and security

Input: diff against the default branch and relevant specs. Output: verified findings ordered by severity and coverage gaps. Completion: no confirmed blocker remains.

## DevOps and ship

Input: verified branch and infrastructure. Output: production build/config/deployment verdict. Completion: readiness is established, then the user separately chooses manual testing or PR/MR creation.
