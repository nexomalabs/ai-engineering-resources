---
system_name: "Wren: late-delivery vouchers"
version: "1.0.0"
date: "2026-12-21"
organization: "Wrenfield Logistics"
owner: "Sam Whitlock, product manager"
on_call: "Wrenfield AI on-call engineer, 020 7946 0018, at any hour"
---

# System Card: Wren late-delivery vouchers v1.0.0

This is the card the team wrote in the week the feature waited. Every figure in it is illustrative; the phone number is from a range reserved for fiction.

## System Overview

- **Purpose:** When a parcel arrives late, Wren offers the customer a voucher
- **Model:** Wren's support model; the voucher is issued through the orders system, never by the model alone
- **Users:** Customers in Wren's chat, about their own orders

## Safety Evaluations

- Tested before launch: requests for larger vouchers, repeated requests, and claims of lateness for parcels that arrived on time
- Findings: the model agreed to a second voucher when asked twice; the orders system now refuses a second voucher per order

## Safeguards

- The orders system checks lateness from the tracking record before issuing anything
- One voucher per order, enforced by the orders system, not the prompt

## Commitments

- Wren may offer one voucher per late parcel, worth at most £10
- Wren may not promise refunds, compensation beyond the voucher, or delivery dates

## Usage Policy

- Permitted: offering a voucher for a parcel the tracking record shows as late
- Prohibited: vouchers for any other reason; changing an order's value

## Monitoring

- A daily report of every voucher issued, with the order and the amount, goes to the owner
- An alert fires if the day's vouchers exceed twice the trailing average

## Known Limitations

- Lateness is judged from the tracking record, which can lag a delivery by a few hours

## Escalation

- A wrong or disputed voucher reaches the on-call engineer within one hour, at any time
- The owner reviews every incident within two business days
