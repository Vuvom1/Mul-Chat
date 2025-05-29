import base64
import json

import nkeys


def verify_jwt_and_seed(user_jwt, user_seed):
    try:
        parts = user_jwt.split('.')
        if len(parts) != 3:
            return False, "JWT format is invalid, expected 3 parts separated by '.'"

        # Decode the payload
        payload_b64 = parts[1]
        # Add padding if needed
        padding = '=' * (4 - len(payload_b64) % 4) if len(payload_b64) % 4 != 0 else ''
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode('utf-8')
        payload = json.loads(payload_json)
        
        # Lấy subject (khóa công khai của user)
        if 'sub' not in payload:
            return False, "JWT not contain 'sub' field"
        
        user_public_from_jwt = payload['sub']
        username = payload.get('name', 'unknown_user')
        
        # Lấy khóa công khai từ seed
        try:
            kp = nkeys.from_seed(user_seed.encode())
            user_public_from_seed = kp.public_key.decode()
            
            # So sánh
            if user_public_from_jwt != user_public_from_seed:
                return False, f"NKeys not match: JWT public key {user_public_from_jwt} does not match seed public key {user_public_from_seed}"
            
            return True, username
        except Exception as e:
            return False, f"Error while processing NKeys seed: {str(e)}"

    except Exception as e:
        return False, f"Error while verifying JWT: {str(e)}"
    
# user_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJlZDI1NTE5LW5rZXkifQ.eyJqdGkiOiJaU0RKUUpHVTczVEJYMlc2WlNQR0FNMks3WlVYUzU2UlREQVYzS0c1VTdKNDcyNFZONFpBIiwiaWF0IjoxNzQ4NDE1MDEyLCJpc3MiOiJBREdSQzdYVlpCMk1FWENKSkczWkQ2SzVCRTdWRUFDR1NETEhPNURTU0I3STM0WElETkVOWjRVMyIsIm5hbWUiOiJ1c2VyMyIsInN1YiI6IlVCNjUzVzRSUU1SVFcyMkxUSU5FWVRYNDRESkNTTFpYUlY0QjNPRERIT1haUVJYQ0lJU1VLT1c1IiwibmF0cyI6eyJwdWIiOnsiYWxsb3ciOlsiYW5vdGhlci5zdWJqZWN0Llx1MDAzZSIsIm5ldy5zdWJqZWN0Llx1MDAzZSJdLCJkZW55IjpbIm5ldy5kZW55cHViIl19LCJzdWIiOnt9LCJzdWJzIjotMSwiZGF0YSI6LTEsInBheWxvYWQiOi0xLCJ0eXBlIjoidXNlciIsInZlcnNpb24iOjJ9fQ.ZpSffkgAw-Rq-0Vh36tMS-_1J2NcQgqr5TPl9l7UBEvtaG41I8IqUtZi5xs5ieCmlEiUx64G2z7qOp8CYrLHBQ"
# user_seed = "SUACOCAI2M6SHL2BQNTBTAFQUAY2VJW2TNGBSZXWGBDT63JYANMTMHPJME"

# is_valid, message = verify_jwt_and_seed(user_jwt, user_seed)
# print(f"Kết quả: {is_valid}, Thông báo: {message}")