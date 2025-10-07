"""Stripe payment integration for subscription management."""

import stripe
import os
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')


class PaymentManager:
    """Handle Stripe payment operations."""

    CONTRIBUTOR_PRICE_ID = os.getenv('STRIPE_CONTRIBUTOR_PRICE_ID', '')
    CONTRIBUTOR_AMOUNT = 500  # $5.00 in cents

    @staticmethod
    def create_checkout_session(user_email: str, user_id: int, success_url: str, cancel_url: str):
        """
        Create a Stripe checkout session for Contributor tier.

        Args:
            user_email: User's email address
            user_id: User ID to track the purchase
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled

        Returns:
            Checkout session object with URL
        """
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Contributor Tier - Monthly',
                            'description': '30 email sends per month + 10 campaigns',
                        },
                        'unit_amount': PaymentManager.CONTRIBUTOR_AMOUNT,
                        'recurring': {
                            'interval': 'month',
                        }
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user_email,
                client_reference_id=str(user_id),
                metadata={
                    'user_id': user_id,
                    'tier': 'CONTRIBUTOR'
                }
            )
            return session
        except Exception as e:
            print(f"Error creating checkout session: {e}")
            return None

    @staticmethod
    def create_customer_portal_session(customer_id: str, return_url: str):
        """
        Create a customer portal session for managing subscription.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after managing subscription

        Returns:
            Portal session object with URL
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session
        except Exception as e:
            print(f"Error creating portal session: {e}")
            return None

    @staticmethod
    def verify_webhook(payload: bytes, sig_header: str) -> dict:
        """
        Verify and parse a Stripe webhook event.

        Args:
            payload: Raw request body
            sig_header: Stripe signature header

        Returns:
            Parsed event object or None if verification fails
        """
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event
        except ValueError:
            # Invalid payload
            return None
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return None

    @staticmethod
    def handle_successful_payment(session):
        """
        Extract payment info from successful checkout session.

        Args:
            session: Stripe checkout session object

        Returns:
            Dictionary with payment information
        """
        return {
            'user_id': session.get('client_reference_id'),
            'customer_id': session.get('customer'),
            'subscription_id': session.get('subscription'),
            'tier': session.get('metadata', {}).get('tier', 'CONTRIBUTOR')
        }
