
import requests
import random
import time
from typing import Dict, Optional, List


class PayChanguAPI:
    """
    PayChangu API Client
    
    Usage:
        api = PayChanguAPI(api_key="your_api_key")
        result = api.create_payment(amount=1000, email="user@email.com", ...)
    """
    
    def __init__(self, api_key: str):
        #Initialize with API key
        self.api_key = api_key
        self.base_url = "https://api.paychangu.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _generate_reference(self, prefix: str = "tx") -> str:
        #Generate unique transaction reference
        timestamp = int(time.time())
        random_num = random.randint(100000, 999999)
        return f"{prefix}_{timestamp}_{random_num}"
    
    def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        #Make HTTP request to PayChangu API
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return {
                "success": response.status_code in [200, 201],
                "status_code": response.status_code,
                "data": response.json() if response.text else {},
                "raw_response": response.text
            }
            
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def create_payment(self, amount: float, email: str, first_name: str, 
                      last_name: str, callback_url: str, return_url: str,
                      currency: str = "MWK", description: str = None) -> Dict:
        """
        Create a payment checkout session
        
        Args:
            amount: Payment amount
            email: Customer email
            first_name: Customer first name
            last_name: Customer last name
            callback_url: Webhook URL for payment updates
            return_url: URL to redirect after payment
            currency: Currency code (default: MWK)
            description: Payment description
            
        Returns:
            dict: Payment response with checkout_url and tx_ref
        """
        tx_ref = self._generate_reference("payment")
        
        payload = {
            "amount": str(amount),
            "currency": currency,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "callback_url": callback_url,
            "return_url": return_url,
            "tx_ref": tx_ref
        }
        
        if description:
            payload["customization"] = {
                "title": "Payment",
                "description": description
            }
        
        response = self._make_request("POST", "/payment", payload)
        
        if response["success"] and response["data"].get("status") == "success":
            checkout_data = response["data"].get("data", {})
            return {
                "success": True,
                "checkout_url": checkout_data.get("checkout_url"),
                "tx_ref": tx_ref,
                "message": "Payment created successfully"
            }
        else:
            return {
                "success": False,
                "message": response["data"].get("message", "Payment creation failed"),
                "tx_ref": tx_ref
            }
    
    def verify_payment(self, tx_ref: str) -> Dict:
        """
        Verify payment status
        
        Args:
            tx_ref: Transaction reference
            
        Returns:
            dict: Payment verification result
        """
        response = self._make_request("GET", f"/payment/verify/{tx_ref}")
        
        if response["success"]:
            return {
                "success": True,
                "data": response["data"].get("data", {}),
                "status": response["data"].get("data", {}).get("status", "unknown")
            }
        else:
            return {
                "success": False,
                "message": "Payment verification failed"
            }
    
    def get_banks(self, currency: str = "MWK") -> List[Dict]:
        """
        Get supported banks for payouts
        
        Args:
            currency: Currency code
            
        Returns:
            list: List of supported banks
        """
        response = self._make_request("GET", f"/direct-charge/payouts/supported-banks?currency={currency}")
        
        if response["success"]:
            return response["data"].get("data", [])
        return []
    
    def create_bank_payout(self, amount: float, bank_uuid: str, 
                          account_name: str, account_number: str) -> Dict:
        """
        Create bank transfer payout
        
        Args:
            amount: Payout amount
            bank_uuid: Bank UUID from get_banks()
            account_name: Bank account name
            account_number: Bank account number
            
        Returns:
            dict: Payout creation result
        """
        charge_id = self._generate_reference("bank_payout")
        
        payload = {
            "payout_method": "bank_transfer",
            "bank_uuid": bank_uuid,
            "amount": str(amount),
            "charge_id": charge_id,
            "bank_account_name": account_name,
            "bank_account_number": account_number
        }
        
        response = self._make_request("POST", "/direct-charge/payouts/initialize", payload)
        
        if response["success"] and response["data"].get("status") == "success":
            transaction = response["data"].get("data", {}).get("transaction", {})
            return {
                "success": True,
                "ref_id": transaction.get("ref_id"),
                "status": transaction.get("status"),
                "charge_id": charge_id,
                "message": "Bank payout created successfully"
            }
        else:
            return {
                "success": False,
                "message": response["data"].get("message", "Bank payout failed"),
                "charge_id": charge_id
            }
    
    def create_mobile_payout(self, amount: float, mobile_number: str) -> Dict:
        """
        Create mobile money payout
        
        Args:
            amount: Payout amount
            mobile_number: Mobile money number
            
        Returns:
            dict: Payout creation result
        """
        charge_id = self._generate_reference("mobile_payout")
        
        # Simple provider detection for Malawi
        if mobile_number.startswith('088') or mobile_number.startswith('+26588'):
            bank_uuid = "e8d5fca0-e5ac-4714-a518-484be9011326"  # Airtel Money
        else:
            bank_uuid = "5e9946ae-76ed-43f5-ad59-63e09096006a"  # TNM Mpamba
        
        payload = {
            "payout_method": "mobile_money",
            "bank_uuid": bank_uuid,
            "amount": str(amount),
            "charge_id": charge_id,
            "mobile_number": mobile_number
        }
        
        response = self._make_request("POST", "/direct-charge/payouts/initialize", payload)
        
        if response["success"] and response["data"].get("status") == "success":
            transaction = response["data"].get("data", {}).get("transaction", {})
            return {
                "success": True,
                "ref_id": transaction.get("ref_id"),
                "status": transaction.get("status"),
                "charge_id": charge_id,
                "message": "Mobile payout created successfully"
            }
        else:
            return {
                "success": False,
                "message": response["data"].get("message", "Mobile payout failed"),
                "charge_id": charge_id
            }
    
    def verify_payout(self, ref_id: str) -> Dict:
        """
        Verify payout status
        
        Args:
            ref_id: Payout reference ID
            
        Returns:
            dict: Payout verification result
        """
        response = self._make_request("GET", f"/direct-charge/payouts/verify/{ref_id}")
        
        if response["success"]:
            data = response["data"].get("data", {})
            return {
                "success": True,
                "status": data.get("status"),
                "details": data
            }
        else:
            return {
                "success": False,
                "message": "Payout verification failed"
            }


# usage example
if __name__ == "__main__":
    # Initialize API
    api = PayChanguAPI("your_api_key_here")
    
    # Create payment
    payment_result = api.create_payment(
        amount=1000.0,
        email="customer@example.com",
        first_name="John",
        last_name="Doe",
        callback_url="https://yoursite.com/callback",
        return_url="https://yoursite.com/return",
        description="Test payment"
    )
    
    print("Payment Result:", payment_result)
    
    # Verify payment
    if payment_result["success"]:
        verify_result = api.verify_payment(payment_result["tx_ref"])
        print("Verification Result:", verify_result)
    
    # Get banks
    banks = api.get_banks()
    print("Available Banks:", len(banks))
    
    # Create mobile payout
    payout_result = api.create_mobile_payout(
        amount=500.0,
        mobile_number="0881234567"
    )
    print("Payout Result:", payout_result)