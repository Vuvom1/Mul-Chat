import logging
import os
import base64
import json
import tempfile

logger = logging.getLogger(__name__)

def extract_jwt_and_nkeys_seed_from_file(creds_file: str):
    try:
        # Expand the tilde in the path to the user's home directory
        expanded_path = os.path.expanduser(creds_file)
        
        # Check if file exists
        if not os.path.exists(expanded_path):
            logger.error(f"Credentials file not found: {expanded_path}")
            return None, None, None, None
            
        with open(expanded_path, 'r') as f:
            content = f.read()
            
        # Rest of your existing code...
        # Extract JWT
        jwt_start = content.find("-----BEGIN NATS USER JWT-----") + len("-----BEGIN NATS USER JWT-----")
        jwt_end = content.find("------END NATS USER JWT------")
        if jwt_start == -1 or jwt_end == -1:
            logger.error(f"JWT section not found in credentials file: {expanded_path}")
            return None, None, None, None
            
        jwt = content[jwt_start:jwt_end].strip()
            
        # Extract seed
        seed_start = content.find("-----BEGIN USER NKEY SEED-----") + len("-----BEGIN USER NKEY SEED-----")
        seed_end = content.find("------END USER NKEY SEED------")
        if seed_start == -1 or seed_end == -1:
            logger.error(f"Seed section not found in credentials file: {expanded_path}")
            return jwt, None, None, None
            
        seed = content[seed_start:seed_end].strip()
        
        # Extract public key and account public key from JWT
        jwt_parts = jwt.split('.')
        if len(jwt_parts) < 2:
            logger.error(f"Invalid JWT format in credentials file: {expanded_path}")
            return jwt, seed, None, None
            
        try:
            # Add padding if needed for base64 decoding
            padded = jwt_parts[1] + '=' * (-len(jwt_parts[1]) % 4)
            payload = base64.urlsafe_b64decode(padded)
            jwt_data = json.loads(payload)
                
            # Extract public key (sub field in JWT)
            public_key = jwt_data.get('sub')
                
            # Extract account public key (iss field in JWT)
            account_public_key = jwt_data.get('iss')
                
            return jwt, seed, public_key, account_public_key
        except Exception as e:
            logger.error(f"Error decoding JWT data: {e}")
            return jwt, seed, None, None
                
    except Exception as e:
        logger.error(f"Error parsing credentials file {creds_file}: {e}")
        return None, None, None, None
    
def sign_nounce(nkeys_seed: str, nonce: str):
    try:
        import nkeys
        seed = nkeys.from_seed(nkeys_seed)
        return seed.sign(nonce.encode()).decode()
    except Exception as e:
        logger.error(f"Error signing nonce: {e}")
        return None
    
def create_nats_creds_file(jwt: str, seed: str) -> str:
    """
    Creates a NATS credentials file from JWT and seed
    
    Args:
        jwt: The NATS JWT
        seed: The NKeys seed
        
    Returns:
        str: Path to the temporary credentials file
    """
    try:
        # Format the content according to NATS creds file format
        content = (
            f"-----BEGIN NATS USER JWT-----\n"
            f"{jwt}\n"
            f"------END NATS USER JWT------\n\n"
            f"-----BEGIN USER NKEY SEED-----\n"
            f"{seed}\n"
            f"------END USER NKEY SEED------\n"
        )
        
        # Write to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
            temp.write(content)
            return temp.name
    except Exception as e:
        logger.error(f"Error creating NATS credentials file: {str(e)}")
        raise