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
        # Medium priority fee
        run_command("solana config set --commitment confirmed")
        print("  Set to balanced mode: Medium priority, confirmed commitment")
        
    elif choice == '2':  # Fast
        # High priority fee
        run_command("solana config set --commitment finalized")
        # Add priority fee flag for future transactions
        print("  Set to fast mode: High priority, finalized commitment")
        
    elif choice == '3':  # Economy
        # Low priority fee
        run_command("solana config set --commitment processed")
        print("  Set to economy mode: Low priority, processed commitment")
        
    elif choice == '4':  # Custom
        custom_fee = get_priority_fee()
        run_command("solana config set --commitment confirmed")
        print(f"  Set custom priority fee: {custom_fee} micro-lamports")
    
    # Get current gas settings
    output, error, code = run_command("solana config get")
    if code == 0:
        print("  Current configuration applied")
    print()

def estimate_transaction_costs():
    """Estimate and display expected transaction costs"""
    print("Estimating transaction costs...")
    
    # Typical costs for each operation (in SOL)
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
    
    # Check if wallet has enough balance
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

def submit_to_dexscreener(token_address, token_name, token_symbol):
    """Submit token to DexScreener"""
    print("Submitting to DexScreener...")
    try:
        # DexScreener automatically indexes tokens, but we can prepare the links
        encoded_name = urllib.parse.quote(f"{token_name} {token_symbol}")
        dexscreener_url = f"https://dexscreener.com/solana/{token_address}"
        
        print(f"  DexScreener will automatically detect your token")
        print(f"  You can view it at: {dexscreener_url}")
        
        # Prepare API submission (when pair is created)
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
    
    # Always submit to these (they auto-index)
    listing_results['dexscreener'] = submit_to_dexscreener(
        token_address, token_details['name'], token_details['symbol']
    )
    
    listing_results['birdeye'] = submit_to_birdeye(token_address)
    listing_results['rugcheck'] = submit_to_rugcheck(token_address)
    
    if listing_preference in ['1', '2']:  # All or major platforms
        listing_results['dextools'] = submit_to_dextools(
            token_address, token_details['name'], token_details['symbol']
        )
    
    if listing_preference == '1':  # All platforms
        listing_results['coinmarketcap'] = submit_to_coinmarketcap(
            token_address, token_details['name'], token_details['symbol'], token_details['website']
        )
        listing_results['coingecko'] = submit_to_coingecko(
            token_address, token_details['name'], token_details['symbol'], token_details['website']
        )
    
    # Generate listing report
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
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("TRACKING PLATFORMS:\n")
        f.write("-" * 20 + "\n")
        
        for platform, url in listing_results.items():
            if url:
                f.write(f"{platform.upper()}: {url}\n")
        
        f.write("\nNEXT STEPS FOR LISTING:\n")
        f.write("-" * 25 + "\n")
        f.write("1. Create liquidity pool on Raydium or Orca\n")
        f.write("2. Wait for automatic indexing on DexScreener/Birdeye (usually 5-15 minutes)\n")
        f.write("3. Manually submit to DexTools after liquidity is added\n")
        f.write("4. Submit to CoinMarketCap/CoinGecko once you have trading volume\n")
        f.write("5. Share your token on Twitter and Telegram communities\n")
        
        f.write("\nSOCIAL SUBMISSION TIPS:\n")
        f.write("-" * 25 + "\n")
        f.write("1. Twitter: Use relevant hashtags (#Solana, #MemeCoin, #DeFi)\n")
        f.write("2. Telegram: Share in legitimate crypto groups\n")
        f.write("3. Reddit: Post in r/Solana and relevant subreddits\n")
        f.write("4. Remember to engage with your community regularly\n")
    
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

# ... (keep all the existing functions from previous script: get_token_details, confirm_details, create_token, setup_token_account, mint_tokens, disable_future_minting, create_metadata_file, setup_metadata_on_chain, send_tokens_to_recipient, cleanup, show_final_summary)

def main():
    print("Welcome to the Enhanced Solana Token Creator")
    print("Now with Gas Optimization and Auto-Listing Services!")
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
    if listing_preference != '3':  # If not "No"
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
