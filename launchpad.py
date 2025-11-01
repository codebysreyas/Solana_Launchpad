#!/usr/bin/env python3

import subprocess
import json
import os
import sys
import time
import requests
import urllib.parse

def run_command(cmd):
    """Execute a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return None, str(e), 1

def check_dependencies():
    """Check if required tools are installed"""
    print("Checking if we have everything we need...")
    
    dependencies = {
        'solana': 'Solana CLI tools',
        'spl-token': 'SPL Token program (install with: npm install -g @solana/spl-token)',
        'metaplex': 'Metaplex CLI (install with: npm install -g @metaplex-foundation/cli)'
    }
    
    missing = []
    for cmd, description in dependencies.items():
        output, error, code = run_command(f"which {cmd}")
        if code != 0:
            missing.append(f"{cmd} - {description}")
        else:
            print(f"  Found {cmd}")
    
    if missing:
        print("\nSorry, we're missing some required tools:")
        for item in missing:
            print(f"  - {item}")
        print("\nPlease install these first and then run the script again.")
        sys.exit(1)
    
    print("Great! All required tools are available.\n")

def get_gas_optimization_preference():
    """Ask user about gas optimization preferences"""
    print("\nGas Fee Optimization:")
    print("How would you like to handle transaction fees?")
    print("  1) Balanced (Recommended) - Good speed, reasonable cost")
    print("  2) Fast - Higher priority, faster confirmation")
    print("  3) Economy - Lower cost, may take longer")
    print("  4) Custom - Set specific priority fee")
    
    while True:
        choice = input("Please enter 1, 2, 3, or 4: ").strip()
        if choice in ['1', '2', '3', '4']:
            return choice
        else:
            print("That's not a valid choice. Please enter 1, 2, 3, or 4.")

def get_priority_fee():
    """Get custom priority fee from user"""
    while True:
        try:
            fee = input("Enter priority fee in micro-lamports (e.g., 100000 for 0.0001 SOL): ").strip()
            fee = int(fee)
            if fee >= 0:
                return fee
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")

def optimize_gas_settings(choice):
    """Configure gas settings based on user preference"""
    print("Configuring transaction settings...")
    
    if choice == '1':  # Balanced
        run_command("solana config set --commitment confirmed")
        print("  Set to balanced mode: Medium priority, confirmed commitment")
        
    elif choice == '2':  # Fast
        run_command("solana config set --commitment finalized")
        print("  Set to fast mode: High priority, finalized commitment")
        
    elif choice == '3':  # Economy
        run_command("solana config set --commitment processed")
        print("  Set to economy mode: Low priority, processed commitment")
        
    elif choice == '4':  # Custom
        custom_fee = get_priority_fee()
        run_command("solana config set --commitment confirmed")
        print(f"  Set custom priority fee: {custom_fee} micro-lamports")
    
    output, error, code = run_command("solana config get")
    if code == 0:
        print("  Current configuration applied")
    print()

def estimate_transaction_costs():
    """Estimate and display expected transaction costs"""
    print("Estimating transaction costs...")
    
    costs = {
        "Create Token": 0.002,
        "Create Token Account": 0.002,
        "Mint Tokens": 0.0005,
        "Create Metadata": 0.01,
        "Transfer Tokens": 0.0005,
    }
    
    total_estimate = sum(costs.values())
    
    print("  Expected transaction breakdown:")
    for operation, cost in costs.items():
        print(f"    {operation}: {cost:.6f} SOL")
    
    print(f"  Total estimated cost: {total_estimate:.6f} SOL")
    
    balance_output, error, code = run_command("solana balance")
    if code == 0:
        try:
            current_balance = float(balance_output.split()[0])
            if current_balance < total_estimate:
                print(f"  Warning: Your balance ({current_balance:.6f} SOL) might be low for all transactions")
                print("  Consider getting more SOL or using economy mode")
            else:
                print("  Your balance appears sufficient for all operations")
        except:
            print("  Could not verify balance against estimated costs")
    
    print()

def get_auto_listing_preference():
    """Ask user about auto-listing preferences"""
    print("\nAuto-Listing Services:")
    print("Would you like to automatically submit your token to tracking sites?")
    print("  1) Yes, submit to all available services")
    print("  2) Only submit to major platforms (DexScreener, DexTools)")
    print("  3) No, I'll do this manually later")
    
    while True:
        choice = input("Please enter 1, 2, or 3: ").strip()
        if choice in ['1', '2', '3']:
            return choice
        else:
            print("That's not a valid choice. Please enter 1, 2, or 3.")

def get_circulating_supply_info(total_supply):
    """Get circulating supply information from user"""
    print("\nCirculating Supply Configuration:")
    print("This helps prevent fake market cap claims by being transparent about token distribution.")
    print(f"Total Supply: {total_supply:,} tokens")
    
    while True:
        try:
            circulating_input = input(f"Circulating Supply (tokens available to trade): ")
            circulating_supply = int(circulating_input)
            
            if circulating_supply <= 0:
                print("Circulating supply must be greater than 0.")
                continue
                
            if circulating_supply > total_supply:
                print(f"Circulating supply cannot be greater than total supply ({total_supply:,}).")
                continue
            
            # Calculate percentages
            circulating_percent = (circulating_supply / total_supply) * 100
            locked_percent = 100 - circulating_percent
            
            print(f"\nSupply Breakdown:")
            print(f"  Circulating: {circulating_supply:,} tokens ({circulating_percent:.1f}%)")
            print(f"  Locked/Reserved: {total_supply - circulating_supply:,} tokens ({locked_percent:.1f}%)")
            
            if circulating_percent < 10:
                print("  Note: Very low circulating supply may be seen as suspicious")
            elif circulating_percent > 90:
                print("  Note: High circulating supply is generally more transparent")
            
            # Ask about lockup details
            print("\nLocked/Reserved Tokens Information (for transparency):")
            lock_reason = input("What are the locked tokens for? (e.g., 'team allocation, marketing, future development'): ")
            
            lock_duration = input("Lock duration (e.g., '6 months', '1 year', 'vesting schedule'): ")
            
            confirm = input("\nDoes this supply distribution look correct? (yes/no): ").lower().strip()
            if confirm in ['yes', 'y']:
                return {
                    'circulating_supply': circulating_supply,
                    'circulating_percent': circulating_percent,
                    'locked_supply': total_supply - circulating_supply,
                    'locked_percent': locked_percent,
                    'lock_reason': lock_reason,
                    'lock_duration': lock_duration
                }
            else:
                print("Let's try again.")
                
        except ValueError:
            print("Please enter a valid number.")

def submit_to_dexscreener(token_address, token_name, token_symbol):
    """Submit token to DexScreener"""
    print("Submitting to DexScreener...")
    try:
        encoded_name = urllib.parse.quote(f"{token_name} {token_symbol}")
        dexscreener_url = f"https://dexscreener.com/solana/{token_address}"
        
        print(f"  DexScreener will automatically detect your token")
        print(f"  You can view it at: {dexscreener_url}")
        
        return dexscreener_url
    except Exception as e:
        print(f"  Could not prepare DexScreener submission: {e}")
        return None

def submit_to_dextools(token_address, token_name, token_symbol):
    """Prepare DexTools submission"""
    print("Preparing DexTools submission...")
    try:
        dextools_url = f"https://www.dextools.io/app/en/solana/pair-explorer/{token_address}"
        
        print(f"  Once you create a liquidity pool, submit to DexTools:")
        print(f"  {dextools_url}")
        
        return dextools_url
    except Exception as e:
        print(f"  Could not prepare DexTools submission: {e}")
        return None

def submit_to_coinmarketcap(token_address, token_name, token_symbol, website):
    """Prepare CoinMarketCap submission"""
    print("Preparing CoinMarketCap submission...")
    try:
        cmc_url = "https://developer.coinmarketcap.com/community/submit-asset/"
        
        print(f"  Submit your token to CoinMarketCap:")
        print(f"  {cmc_url}")
        print(f"  You'll need: Token address, website, social links")
        
        return cmc_url
    except Exception as e:
        print(f"  Could not prepare CoinMarketCap submission: {e}")
        return None

def submit_to_coingecko(token_address, token_name, token_symbol, website):
    """Prepare CoinGecko submission"""
    print("Preparing CoinGecko submission...")
    try:
        coingecko_url = "https://www.coingecko.com/en/coins/submit"
        
        print(f"  Submit your token to CoinGecko:")
        print(f"  {coingecko_url}")
        print(f"  You'll need detailed project information")
        
        return coingecko_url
    except Exception as e:
        print(f"  Could not prepare CoinGecko submission: {e}")
        return None

def submit_to_birdeye(token_address):
    """Submit token to Birdeye"""
    print("Submitting to Birdeye...")
    try:
        birdeye_url = f"https://birdeye.so/token/{token_address}?chain=solana"
        
        print(f"  Birdeye will automatically index your token")
        print(f"  You can view it at: {birdeye_url}")
        
        return birdeye_url
    except Exception as e:
        print(f"  Could not prepare Birdeye submission: {e}")
        return None

def submit_to_rugcheck(token_address):
    """Submit token to RugCheck"""
    print("Submitting to RugCheck...")
    try:
        rugcheck_url = f"https://rugcheck.xyz/tokens/{token_address}"
        
        print(f"  RugCheck will analyze your token's security")
        print(f"  You can view it at: {rugcheck_url}")
        
        return rugcheck_url
    except Exception as e:
        print(f"  Could not prepare RugCheck submission: {e}")
        return None

def auto_list_token(token_address, token_details, listing_preference):
    """Handle all auto-listing submissions"""
    print("\n" + "="*50)
    print("Starting Auto-Listing Process")
    print("="*50)
    
    listing_results = {}
    
    listing_results['dexscreener'] = submit_to_dexscreener(
        token_address, token_details['name'], token_details['symbol']
    )
    
    listing_results['birdeye'] = submit_to_birdeye(token_address)
    listing_results['rugcheck'] = submit_to_rugcheck(token_address)
    
    if listing_preference in ['1', '2']:
        listing_results['dextools'] = submit_to_dextools(
            token_address, token_details['name'], token_details['symbol']
        )
    
    if listing_preference == '1':
        listing_results['coinmarketcap'] = submit_to_coinmarketcap(
            token_address, token_details['name'], token_details['symbol'], token_details['website']
        )
        listing_results['coingecko'] = submit_to_coingecko(
            token_address, token_details['name'], token_details['symbol'], token_details['website']
        )
    
    generate_listing_report(listing_results, token_address, token_details)
    
    return listing_results

def generate_listing_report(listing_results, token_address, token_details):
    """Generate a comprehensive listing report"""
    print("\n" + "="*50)
    print("AUTO-LISTING REPORT")
    print("="*50)
    
    report_file = f"token_listing_report_{token_address[:8]}.txt"
    
    with open(report_file, 'w') as f:
        f.write("TOKEN LISTING SUBMISSION REPORT\n")
        f.write("=" * 40 + "\n\n")
        
        f.write(f"Token: {token_details['name']} ({token_details['symbol']})\n")
        f.write(f"Address: {token_address}\n")
        f.write(f"Total Supply: {token_details['supply']:,}\n")
        if 'circulating_info' in token_details:
            f.write(f"Circulating Supply: {token_details['circulating_info']['circulating_supply']:,}\n")
            f.write(f"Circulating Percentage: {token_details['circulating_info']['circulating_percent']:.1f}%\n")
            f.write(f"Locked Tokens: {token_details['circulating_info']['locked_supply']:,}\n")
            f.write(f"Lock Reason: {token_details['circulating_info']['lock_reason']}\n")
            f.write(f"Lock Duration: {token_details['circulating_info']['lock_duration']}\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("TRACKING PLATFORMS:\n")
        f.write("-" * 20 + "\n")
        
        for platform, url in listing_results.items():
            if url:
                f.write(f"{platform.upper()}: {url}\n")
        
        f.write("\nSUPPLY TRANSPARENCY NOTE:\n")
        f.write("-" * 25 + "\n")
        if 'circulating_info' in token_details:
            f.write("You have configured transparent supply information.\n")
            f.write("This helps build trust with investors by being clear about token distribution.\n")
            f.write(f"Circulating Supply: {token_details['circulating_info']['circulating_supply']:,} tokens\n")
            f.write(f"Locked/Reserved: {token_details['circulating_info']['locked_supply']:,} tokens\n")
            f.write(f"Lock Reason: {token_details['circulating_info']['lock_reason']}\n")
            f.write(f"Lock Duration: {token_details['circulating_info']['lock_duration']}\n")
        else:
            f.write("Consider being transparent about your token supply distribution\n")
            f.write("to build trust with potential investors.\n")
        
        f.write("\nNEXT STEPS FOR LISTING:\n")
        f.write("-" * 25 + "\n")
        f.write("1. Create liquidity pool on Raydium or Orca\n")
        f.write("2. Wait for automatic indexing on DexScreener/Birdeye (usually 5-15 minutes)\n")
        f.write("3. Manually submit to DexTools after liquidity is added\n")
        f.write("4. Submit to CoinMarketCap/CoinGecko once you have trading volume\n")
        f.write("5. Share your token on Twitter and Telegram communities\n")
        
        f.write("\nSOCIAL SUBMISSION TIPS:\n")
        f.write("-" * 25 + "\n")
        f.write("1. Be transparent about token supply and distribution\n")
        f.write("2. Share your circulating supply information to build trust\n")
        f.write("3. Explain what locked tokens are for and when they unlock\n")
        f.write("4. Use relevant hashtags (#Solana, #MemeCoin, #DeFi)\n")
        f.write("5. Engage with your community regularly\n")
    
    print(f"Complete listing report saved to: {report_file}")
    print("This file contains all the links and next steps for promoting your token.")

def get_wallet_choice():
    """Ask user which wallet to use"""
    print("Which wallet would you like to use for creating the token?")
    print("  1) Use current default wallet")
    print("  2) Use a custom wallet file")
    print("  3) Use a different wallet by its keypair")
    
    while True:
        choice = input("Please enter 1, 2, or 3: ").strip()
        if choice == '1':
            return 'default', None
        elif choice == '2':
            return 'file', get_wallet_file_path()
        elif choice == '3':
            return 'keypair', get_wallet_keypair()
        else:
            print("That's not a valid choice. Please enter 1, 2, or 3.")

def get_wallet_file_path():
    """Get the path to a custom wallet file"""
    while True:
        path = input("Enter the path to your wallet keypair file: ").strip()
        if os.path.exists(path):
            return path
        else:
            print("That file doesn't exist. Please check the path and try again.")

def get_wallet_keypair():
    """Get a wallet keypair directly"""
    print("You can enter the keypair as:")
    print("  - A base58 encoded string")
    print("  - Or paste the JSON array (looks like [1,2,3,...])")
    keypair_input = input("Enter your wallet keypair: ").strip()
    
    if keypair_input.startswith('[') and keypair_input.endswith(']'):
        try:
            json.loads(keypair_input)
            temp_path = "/tmp/temp_wallet_keypair.json"
            with open(temp_path, 'w') as f:
                f.write(keypair_input)
            return temp_path
        except json.JSONDecodeError:
            print("That doesn't look like valid JSON. Please try again.")
            return get_wallet_keypair()
    else:
        try:
            temp_path = "/tmp/temp_wallet_keypair.json"
            with open(temp_path, 'w') as f:
                f.write('["base58_key", "' + keypair_input + '"]')
            return temp_path
        except:
            print("There was a problem with that keypair. Please try again.")
            return get_wallet_keypair()

def set_wallet(wallet_type, wallet_path):
    """Set the Solana CLI to use the specified wallet"""
    if wallet_type == 'default':
        return True
    elif wallet_type == 'file' or wallet_type == 'keypair':
        if wallet_path and os.path.exists(wallet_path):
            output, error, code = run_command(f"solana config set --keypair {wallet_path}")
            return code == 0
    return False

def get_network_choice():
    """Ask user which network to use"""
    print("Which network would you like to use?")
    print("  1) Devnet (good for testing, uses fake SOL)")
    print("  2) Mainnet (real SOL, real money)")
    
    while True:
        choice = input("Please enter 1 or 2: ").strip()
        if choice == '1':
            return 'devnet'
        elif choice == '2':
            return 'mainnet-beta'
        else:
            print("That's not a valid choice. Please enter 1 for devnet or 2 for mainnet.")

def check_wallet_status(network, wallet_type, wallet_path):
    """Check and display wallet information"""
    print("Let me check your wallet...")
    
    run_command(f"solana config set --url {network}")
    
    if wallet_type != 'default':
        if not set_wallet(wallet_type, wallet_path):
            return None, None
    
    address, error, code = run_command("solana address")
    if code != 0:
        print("I couldn't find your wallet address. Make sure your Solana wallet is set up correctly.")
        return None, None
    
    balance, error, code = run_command("solana balance")
    if code != 0:
        balance = "Unknown"
    
    print(f"  Wallet address: {address}")
    print(f"  Current balance: {balance}")
    print(f"  Network: {network}\n")
    
    return address, balance

def offer_devnet_airdrop(network, wallet_type, wallet_path):
    """Offer to airdrop SOL on devnet"""
    if network != 'devnet':
        return
    
    choice = input("Would you like to get some test SOL from the devnet faucet? (yes/no): ").lower().strip()
    if choice in ['yes', 'y']:
        print("Requesting test SOL from the devnet faucet...")
        
        if wallet_type != 'default':
            set_wallet(wallet_type, wallet_path)
        
        output, error, code = run_command("solana airdrop 2")
        if code == 0:
            print("Success! You should now have some test SOL.")
        else:
            print("The airdrop didn't work. You might need to try again later.")
        print()

def get_token_details(wallet_address):
    """Get all the token details from the user"""
    print("\nNow let's configure your token. I'll need some information:")
    print("="*50)
    
    # Basic token information
    print("\nBasic Token Information:")
    print("-" * 20)
    token_name = input("Token Name: ")
    token_symbol = input("Token Symbol: ")
    
    while True:
        decimals_input = input("Decimals (usually 6 or 9 for meme coins): ")
        if decimals_input.isdigit():
            decimals = int(decimals_input)
            if decimals <= 18:
                break
            else:
                print("That's quite high. Most tokens use 6-9 decimals.")
        else:
            print("Please enter a number like 6 or 9.")
    
    while True:
        supply_input = input("Total Supply: ")
        if supply_input.isdigit():
            total_supply = int(supply_input)
            if total_supply > 0:
                break
            else:
                print("Supply should be greater than 0.")
        else:
            print("Please enter a valid number.")
    
    # Circulating supply configuration
    circulating_info = get_circulating_supply_info(total_supply)
    
    # Token appearance
    print("\nToken Appearance:")
    print("-" * 20)
    logo_url = input("Logo URL (image must be publicly accessible): ")
    description = input("Description: ")
    
    # Creator information
    print("\nCreator Information:")
    print("-" * 20)
    print(f"Current wallet: {wallet_address}")
    creator_address = input("Creator wallet address (press Enter to use current wallet): ").strip()
    if not creator_address:
        creator_address = wallet_address
    
    creator_name = input("Creator name (optional): ")
    creator_website = input("Creator website (optional): ")
    
    # Social links and tags
    print("\nSocial Links & Tags:")
    print("-" * 20)
    website = input("Token website URL: ")
    twitter = input("Twitter URL: ")
    telegram = input("Telegram URL: ")
    discord = input("Discord URL (optional): ")
    github = input("GitHub URL (optional): ")
    
    # Tags
    print("\nAdd some tags to describe your token (comma-separated):")
    print("Example: meme, defi, gaming, nft")
    tags_input = input("Tags: ").strip()
    tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
    
    # Token recipient
    print("\nToken Distribution:")
    print("-" * 20)
    recipient = input("Token recipient wallet address: ")
    
    return {
        'name': token_name,
        'symbol': token_symbol,
        'decimals': decimals,
        'supply': total_supply,
        'circulating_info': circulating_info,
        'logo': logo_url,
        'description': description,
        'creator_address': creator_address,
        'creator_name': creator_name,
        'creator_website': creator_website,
        'website': website,
        'twitter': twitter,
        'telegram': telegram,
        'discord': discord,
        'github': github,
        'tags': tags,
        'recipient': recipient
    }

def confirm_details(details, network, wallet_address):
    """Show the user all details and confirm before proceeding"""
    print("\n" + "="*60)
    print("Please review all the details:")
    print("="*60)
    
    print("\nBASIC TOKEN INFORMATION:")
    print(f"  Token Name: {details['name']}")
    print(f"  Token Symbol: {details['symbol']}")
    print(f"  Decimals: {details['decimals']}")
    print(f"  Total Supply: {details['supply']:,}")
    
    if 'circulating_info' in details:
        print("\nSUPPLY DISTRIBUTION:")
        print(f"  Circulating Supply: {details['circulating_info']['circulating_supply']:,} tokens")
        print(f"  Circulating Percentage: {details['circulating_info']['circulating_percent']:.1f}%")
        print(f"  Locked/Reserved: {details['circulating_info']['locked_supply']:,} tokens")
        print(f"  Lock Reason: {details['circulating_info']['lock_reason']}")
        print(f"  Lock Duration: {details['circulating_info']['lock_duration']}")
    
    print("\nTOKEN APPEARANCE:")
    print(f"  Logo URL: {details['logo']}")
    print(f"  Description: {details['description']}")
    
    print("\nCREATOR INFORMATION:")
    print(f"  Creator Wallet: {details['creator_address']}")
    if details['creator_name']:
        print(f"  Creator Name: {details['creator_name']}")
    if details['creator_website']:
        print(f"  Creator Website: {details['creator_website']}")
    
    print("\nSOCIAL LINKS:")
    print(f"  Website: {details['website']}")
    print(f"  Twitter: {details['twitter']}")
    print(f"  Telegram: {details['telegram']}")
    if details['discord']:
        print(f"  Discord: {details['discord']}")
    if details['github']:
        print(f"  GitHub: {details['github']}")
    
    if details['tags']:
        print(f"  Tags: {', '.join(details['tags'])}")
    
    print("\nDISTRIBUTION:")
    print(f"  Recipient: {details['recipient']}")
    print(f"  Funding Wallet: {wallet_address}")
    print(f"  Network: {network}")
    
    print("="*60)
    
    while True:
        choice = input("\nDoes everything look correct? Would you like to create the token now? (yes/no): ").lower().strip()
        if choice in ['yes', 'y']:
            return True
        elif choice in ['no', 'n']:
            print("No problem. Let's start over or you can run the script again when you're ready.")
            return False
        else:
            print("Please answer yes or no.")

def create_token(decimals, wallet_type, wallet_path):
    """Create the token and return its address"""
    print("\nStep 1: Creating your token on the blockchain...")
    
    if wallet_type != 'default':
        set_wallet(wallet_type, wallet_path)
    
    cmd = f"spl-token create-token --decimals {decimals} --enable-metadata"
    output, error, code = run_command(cmd)
    
    if code != 0:
        print(f"Sorry, I ran into a problem creating the token: {error}")
        return None
    
    for line in output.split('\n'):
        if 'Creating token' in line:
            token_address = line.split()[-1]
            print(f"Success! Token created with address: {token_address}")
            return token_address
    
    print("I created the token but couldn't find its address. This is unusual.")
    return None

def setup_token_account(token_address, wallet_type, wallet_path):
    """Create the token account"""
    print("Step 2: Setting up the token account...")
    
    if wallet_type != 'default':
        set_wallet(wallet_type, wallet_path)
    
    output, error, code = run_command(f"spl-token create-account {token_address}")
    
    if code != 0:
        print(f"Had trouble setting up the token account: {error}")
        return False
    
    print("Token account is ready.")
    return True

def mint_tokens(token_address, supply, wallet_type, wallet_path):
    """Mint the initial supply of tokens"""
    print(f"Step 3: Minting {supply:,} tokens...")
    
    if wallet_type != 'default':
        set_wallet(wallet_type, wallet_path)
    
    output, error, code = run_command(f"spl-token mint {token_address} {supply}")
    
    if code != 0:
        print(f"Couldn't mint the tokens: {error}")
        return False
    
    print(f"Successfully minted {supply:,} tokens.")
    return True

def disable_future_minting(token_address, wallet_type, wallet_path):
    """Disable future minting to make the token fixed supply"""
    print("Step 4: Making sure no more tokens can be created...")
    
    if wallet_type != 'default':
        set_wallet(wallet_type, wallet_path)
    
    output, error, code = run_command(f"spl-token authorize {token_address} mint --disable")
    
    if code != 0:
        print(f"Warning: Couldn't disable future minting: {error}")
        return False
    
    print("Future token creation is now disabled.")
    return True

def create_metadata_file(details):
    """Create the metadata JSON file"""
    print("Step 5: Creating token metadata...")
    
    attributes = []
    
    if details['website']:
        attributes.append({
            "trait_type": "Website",
            "value": details['website']
        })
    
    if details['twitter']:
        attributes.append({
            "trait_type": "Twitter",
            "value": details['twitter']
        })
    
    if details['telegram']:
        attributes.append({
            "trait_type": "Telegram",
            "value": details['telegram']
        })
    
    if details['discord']:
        attributes.append({
            "trait_type": "Discord",
            "value": details['discord']
        })
    
    if details['github']:
        attributes.append({
            "trait_type": "GitHub",
            "value": details['github']
        })
    
    if details['creator_name']:
        attributes.append({
            "trait_type": "Creator",
            "value": details['creator_name']
        })
    
    if details['creator_website']:
        attributes.append({
            "trait_type": "Creator Website",
            "value": details['creator_website']
        })
    
    # Add supply transparency information
    if 'circulating_info' in details:
        attributes.append({
            "trait_type": "Circulating Supply",
            "value": f"{details['circulating_info']['circulating_supply']:,}"
        })
        
        attributes.append({
            "trait_type": "Total Supply", 
            "value": f"{details['supply']:,}"
        })
        
        attributes.append({
            "trait_type": "Lock Reason",
            "value": details['circulating_info']['lock_reason']
        })
        
        attributes.append({
            "trait_type": "Lock Duration",
            "value": details['circulating_info']['lock_duration']
        })
    
    for i, tag in enumerate(details['tags'][:5]):
        attributes.append({
            "trait_type": f"Tag {i+1}",
            "value": tag
        })
    
    metadata = {
        "name": details['name'],
        "symbol": details['symbol'],
        "description": details['description'],
        "image": details['logo'],
        "external_url": details['website'],
        "seller_fee_basis_points": 0,
        "attributes": attributes,
        "properties": {
            "files": [
                {
                    "uri": details['logo'],
                    "type": "image/png"
                }
            ],
            "category": "image",
            "creators": [
                {
                    "address": details['creator_address'],
                    "share": 100
                }
            ]
        }
    }
    
    with open('metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("Token metadata file created with all your information.")

def setup_metadata_on_chain(token_address, wallet_address, network, wallet_type, wallet_path):
    """Set up the metadata on the blockchain"""
    print("Step 6: Adding token information to the blockchain...")
    
    if wallet_type != 'default':
        set_wallet(wallet_type, wallet_path)
    
    upload_cmd = f"metaplex upload metadata.json --env {network}"
    output, error, code = run_command(upload_cmd)
    
    metadata_uri = details['logo']
    
    if code == 0 and output:
        for line in output.split('\n'):
            if 'https://' in line and 'arweave' in line:
                metadata_uri = line.strip()
                print(f"Metadata uploaded to: {metadata_uri}")
                break
    
    metadata_cmd = f"metaplex create_metadata_accounts {token_address} {wallet_address} {wallet_address} {wallet_address} {metadata_uri} '{details['name']}' '{details['symbol']}' --env {network}"
    output, error, code = run_command(metadata_cmd)
    
    if code == 0:
        print("Token information successfully added to blockchain.")
    else:
        print("The token was created but we had trouble adding the information to the blockchain.")

def send_tokens_to_recipient(token_address, recipient, supply, wallet_type, wallet_path):
    """Send tokens to the recipient"""
    print(f"Step 7: Sending tokens to recipient...")
    
    if wallet_type != 'default':
        set_wallet(wallet_type, wallet_path)
    
    print(f"Setting up recipient's token account...")
    run_command(f"spl-token create-account {token_address} --owner {recipient}")
    
    print(f"Sending {supply:,} tokens to {recipient}...")
    output, error, code = run_command(f"spl-token transfer {token_address} {supply} {recipient} --allow-unfunded-recipient")
    
    if code == 0:
        print(f"Successfully sent {supply:,} tokens to the recipient.")
    else:
        print(f"Created the tokens but couldn't send them to the recipient: {error}")

def cleanup():
    """Clean up temporary files"""
    if os.path.exists('metadata.json'):
        os.remove('metadata.json')
    
    for temp_file in ['/tmp/temp_wallet_keypair.json']:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    print("Cleaned up temporary files.")

def show_final_summary(token_address, details, network, wallet_address):
    """Show the final summary to the user"""
    print("\n" + "="*70)
    print("CONGRATULATIONS! Your token has been successfully created!")
    print("="*70)
    
    print(f"\nTOKEN DETAILS:")
    print(f"  Name: {details['name']}")
    print(f"  Symbol: {details['symbol']}")
    print(f"  Address: {token_address}")
    print(f"  Decimals: {details['decimals']}")
    print(f"  Total Supply: {details['supply']:,}")
    
    if 'circulating_info' in details:
        print(f"\nSUPPLY TRANSPARENCY:")
        print(f"  Circulating Supply: {details['circulating_info']['circulating_supply']:,}")
        print(f"  Circulating Percentage: {details['circulating_info']['circulating_percent']:.1f}%")
        print(f"  Locked Tokens: {details['circulating_info']['locked_supply']:,}")
        print(f"  Lock Reason: {details['circulating_info']['lock_reason']}")
        print(f"  Lock Duration: {details['circulating_info']['lock_duration']}")
    
    print(f"\nCREATOR INFORMATION:")
    print(f"  Creator Wallet: {details['creator_address']}")
    if details['creator_name']:
        print(f"  Creator Name: {details['creator_name']}")
    
    print(f"\nLINKS:")
    print(f"  Website: {details['website']}")
    print(f"  Twitter: {details['twitter']}")
    print(f"  Telegram: {details['telegram']}")
    
    if details['tags']:
        print(f"  Tags: {', '.join(details['tags'])}")
    
    print(f"\nDISTRIBUTION:")
    print(f"  Recipient: {details['recipient']}")
    print(f"  Funding Wallet: {wallet_address}")
    print(f"  Network: {network}")
    
    print(f"\nVIEW YOUR TOKEN:")
    print(f"  Solana Explorer: https://explorer.solana.com/address/{token_address}?cluster={network}")
    print(f"  Solscan: https://solscan.io/token/{token_address}?cluster={network}")
    
    print(f"\nSUPPLY TRANSPARENCY NOTE:")
    if 'circulating_info' in details:
        print("  You have configured transparent supply information.")
        print("  This builds trust with investors and prevents fake market cap claims.")
        print("  Be sure to communicate this clearly in your marketing.")
    else:
        print("  Consider being transparent about your token supply distribution")
        print("  to build trust with potential investors.")
    
    print(f"\nNEXT STEPS:")
    print("  1. Consider adding liquidity to a decentralized exchange like Raydium or Orca")
    print("  2. Share your token with your community using the social links you provided")
    print("  3. Be transparent about your circulating supply in all communications")
    print("  4. Verify your token on popular explorers and platforms")
    print("  5. Make sure to keep your wallet secure and never share your private keys")
    
    print("\nThank you for using the Solana Token Creator!")
    print("="*70)

def main():
    print("Welcome to the Enhanced Solana Token Creator")
    print("Now with Circulating Supply Control, Gas Optimization and Auto-Listing Services!")
    print()
    
    # Check dependencies
    check_dependencies()
    
    # Gas optimization setup
    gas_choice = get_gas_optimization_preference()
    optimize_gas_settings(gas_choice)
    estimate_transaction_costs()
    
    # Auto-listing preference
    listing_preference = get_auto_listing_preference()
    
    # Wallet selection
    wallet_type, wallet_path = get_wallet_choice()
    
    # Network selection
    network = get_network_choice()
    
    # Wallet check
    wallet_address, balance = check_wallet_status(network, wallet_type, wallet_path)
    if not wallet_address:
        print("Could not access wallet. Please check your wallet configuration.")
        return
    
    # Offer airdrop on devnet
    if network == 'devnet':
        offer_devnet_airdrop(network, wallet_type, wallet_path)
    
    # Get token details
    global details
    details = get_token_details(wallet_address)
    
    # Confirm everything
    if not confirm_details(details, network, wallet_address):
        return
    
    print("\nStarting the token creation process...")
    print("This might take a minute or two.\n")
    
    # Create the token
    token_address = create_token(details['decimals'], wallet_type, wallet_path)
    if not token_address:
        return
    
    # Set up token account
    if not setup_token_account(token_address, wallet_type, wallet_path):
        return
    
    # Mint tokens
    if not mint_tokens(token_address, details['supply'], wallet_type, wallet_path):
        return
    
    # Disable future minting
    disable_future_minting(token_address, wallet_type, wallet_path)
    
    # Create and set up metadata
    create_metadata_file(details)
    setup_metadata_on_chain(token_address, wallet_address, network, wallet_type, wallet_path)
    
    # Send tokens to recipient
    send_tokens_to_recipient(token_address, details['recipient'], details['supply'], wallet_type, wallet_path)
    
    # Auto-listing services
    if listing_preference != '3':
        listing_results = auto_list_token(token_address, details, listing_preference)
    else:
        listing_results = {}
        print("\nSkipping auto-listing services as requested.")
        print("You can manually submit your token to tracking sites later.")
    
    # Cleanup
    cleanup()
    
    # Show final summary
    show_final_summary(token_address, details, network, wallet_address)
    
    # Add listing results to final output
    if listing_results:
        print("\nAUTO-LISTING RESULTS:")
        print("-" * 20)
        for platform, url in listing_results.items():
            if url:
                print(f"{platform.upper()}: {url}")

if __name__ == "__main__":
    main()
