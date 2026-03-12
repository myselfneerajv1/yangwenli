"""
RUBLI: Generate Indian Mock Data
Generates 10,000 realistic Indian procurement contracts and populates the database.
"""
import sqlite3
import random
import os
import time
from datetime import datetime, timedelta
import uuid
import sys

# Indian states and ministries
STATES = ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Gujarat", "Uttar Pradesh", "West Bengal", "Telangana", "Kerala", "Rajasthan"]

MINISTRIES = [
    ("DEF", "Ministry of Defence", 5),
    ("RHW", "Ministry of Road Transport and Highways", 6),
    ("RLW", "Ministry of Railways", 6),
    ("HUA", "Ministry of Housing and Urban Affairs", 4),
    ("HFW", "Ministry of Health and Family Welfare", 3),
    ("EDU", "Ministry of Education", 3),
    ("IT", "Ministry of Electronics and Information Technology", 4),
    ("FIN", "Ministry of Finance", 2),
    ("AGR", "Ministry of Agriculture and Farmers Welfare", 2),
    ("ENR", "Ministry of New and Renewable Energy", 4)
]

# Random vendor names generator
INDIAN_FIRST_NAMES = ["Amit", "Raj", "Vijay", "Rahul", "Sanjay", "Arun", "Suresh", "Ramesh", "Kiran", "Nitin", "Priya", "Anjali"]
INDIAN_LAST_NAMES = ["Patel", "Sharma", "Singh", "Kumar", "Gupta", "Desai", "Jain", "Reddy", "Rao", "Iyer", "Nair", "Das"]
VENDOR_SUFFIXES = ["Enterprises", "Private Limited", "Pvt Ltd", "Solutions", "Technologies", "Services", "Corporation", "Brothers", "& Co.", "Industries", "Infotech"]

# Sector mapping to categories
SECTORS = [
    (1, "Infrastructure & Construction"),
    (2, "IT & Software Services"),
    (3, "Healthcare & Medical Equipment"),
    (4, "Defense & Security"),
    (5, "Energy & Utilities"),
    (6, "Education & Training"),
    (7, "Consulting & Professional Services"),
    (8, "Transportation & Logistics"),
    (9, "Agriculture & Rural Development"),
    (10, "Office Supplies & Equipment"),
    (11, "Telecommunications"),
    (12, "Other Services")
]

def generate_gstin():
    state_code = f"{random.randint(1, 37):02d}"
    pan = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5)) + \
          "".join(random.choices("0123456789", k=4)) + \
          random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    entity = str(random.randint(1, 9))
    z = "Z"
    checksum = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    return f"{state_code}{pan}{entity}{z}{checksum}"

def random_date(start_year=2002, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    if end > datetime.now():
        end = datetime.now()
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def determine_risk(is_single_bid, is_direct_award, is_december):
    score = random.betavariate(2, 8) # mostly low
    if is_single_bid:
         score += 0.2
    if is_direct_award:
         score += 0.25
    if is_december:
         score += 0.1
         
    # Add random anomaly
    if random.random() < 0.05:
         score += random.uniform(0.3, 0.6)
         
    score = min(score, 1.0)
    
    level = "low"
    if score >= 0.8:
        level = "critical"
    elif score >= 0.5:
        level = "high"
    elif score >= 0.25:
        level = "medium"
        
    return score, level

def main():
    db_path = "RUBLI_NORMALIZED.db"
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found.")
        sys.exit(1)
        
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Clear existing Mexican data from main tables (don't drop schema)
    print("Clearing existing data...")
    cursor.execute("DELETE FROM contracts")
    cursor.execute("DELETE FROM vendors")
    cursor.execute("DELETE FROM institutions")
    cursor.execute("DELETE FROM ministries")
    
    # Create missing anomaly tables if they don't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contract_z_features (
        contract_id INTEGER PRIMARY KEY,
        price_z_score REAL,
        volume_z_score REAL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendor_graph_features (
        vendor_id INTEGER PRIMARY KEY,
        centrality REAL,
        clustering_coeff REAL,
        community_id INTEGER
    )
    """)
    
    # 2. Insert Indian Ministries
    print("Inserting Indian Ministries...")
    ministry_ids = []
    for i, (code, name, sector_id) in enumerate(MINISTRIES, 1):
        try:
            cursor.execute("INSERT INTO ministries (id, clave, descripcion, sector_id) VALUES (?, ?, ?, ?)", (i, code, name, sector_id))
            ministry_ids.append(i)
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                print(f"ERROR: schema is broken: {e}")
                sys.exit(1)
                
    # 3. Generate 300 Indian Institutions
    print("Generating Indian Institutions...")
    institution_ids = []
    for i in range(1, 301):
        min_id = random.choice(ministry_ids)
        ministry_name = MINISTRIES[min_id-1][1]
        state = random.choice(STATES)
        name = f"Department of {random.choice(['Procurement', 'Public Works', 'Development', 'Welfare', 'Infrastructure'])} - {state}"
        clave = f"IND-INST-{i:04d}"
        cursor.execute("INSERT INTO institutions (id, siglas, name, name_normalized, tipo, ramo_id, sector_id, clave_institucion) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (i, f"D{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{i}", name, name.upper(), "Central Government", min_id, MINISTRIES[min_id-1][2], clave))
        institution_ids.append(i)
        
    # 4. Generate 2000 Indian Vendors
    print("Generating Indian Vendors...")
    vendor_ids = []
    for i in range(1, 2001):
        # Generate realistic Indian name
        name_type = random.choice(["person", "company1", "company2"])
        if name_type == "person":
             name = f"{random.choice(INDIAN_FIRST_NAMES)} {random.choice(INDIAN_LAST_NAMES)} {random.choice(VENDOR_SUFFIXES)}"
        elif name_type == "company1":
             name = f"{random.choice(INDIAN_LAST_NAMES)} & {random.choice(INDIAN_LAST_NAMES)} {random.choice(['Associates', 'Co.', 'Brothers'])}"
        else:
             name = f"{random.choice(['Bharat', 'Hindustan', 'National', 'Indian', 'Global', 'Apex'])} {random.choice(SECTORS)[1].split()[0]} {random.choice(VENDOR_SUFFIXES)}"
             
        gstin = generate_gstin()
        is_ghost = 1 if random.random() < 0.02 else 0
        ghost_prob = random.uniform(0.7, 1.0) if is_ghost else random.uniform(0.0, 0.2)
        
        cursor.execute("INSERT INTO vendors (id, gstin, name, name_normalized, is_ghost_company, ghost_probability) VALUES (?, ?, ?, ?, ?, ?)",
                      (i, gstin, name, name.upper(), is_ghost, ghost_prob))
        vendor_ids.append(i)
        
    # 5. Generate 10,000 Procurement Contracts
    print("Generating Indian Procurement Contracts (this may take a minute)...")
    contract_batch = []
    
    for i in range(1, 10001):
        inst_id = random.choice(institution_ids)
        vend_id = random.choice(vendor_ids)
        
        # Get ministry and sector for this institution
        cursor.execute("SELECT ramo_id, sector_id FROM institutions WHERE id = ?", (inst_id,))
        ramo_id, sector_id = cursor.fetchone()
        
        # ... skipped some code just to match the block ...
        date = random_date(2010, 2025)
        is_high_value = 1 if random.random() < 0.05 else 0
        if is_high_value:
             amount_inr = random.uniform(10_000_000, 5_000_000_000)
        else:
             amount_inr = random.uniform(100_000, 10_000_000)
             
        is_direct_award = 1 if random.random() < 0.15 else 0
        is_single_bid = 1 if (not is_direct_award and random.random() < 0.2) else 0
        is_december = 1 if date.month == 12 else 0
        is_election_year = 1 if date.year in [2014, 2019, 2024] else 0
        
        score, level = determine_risk(is_single_bid, is_direct_award, is_december)
        
        contract_number = f"GEM-{date.year}-{random.randint(1000000, 9999999)}"
        c_hash = str(uuid.uuid4())
        
        title_prefix = random.choice(["Procurement of", "Supply of", "Maintenance contract for", "Consultancy for", "Construction of"])
        title = f"{title_prefix} {SECTORS[sector_id-1 if sector_id else 0][1]} services"
        
        contract_batch.append((
            i, vend_id, inst_id, sector_id, ramo_id, contract_number, title, 
            date.strftime('%Y-%m-%d'), amount_inr, 'INR', date.year, date.month,
            is_direct_award, is_single_bid, is_high_value, is_december, is_election_year,
            score, level, c_hash
        ))
        
        if len(contract_batch) >= 1000:
            cursor.executemany("""
                INSERT INTO contracts (
                    id, vendor_id, institution_id, sector_id, ramo_id, contract_number, title,
                    contract_date, amount_inr, currency, contract_year, contract_month,
                    is_direct_award, is_single_bid, is_high_value, is_year_end, is_election_year,
                    risk_score, risk_level, contract_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, contract_batch)
            contract_batch = []
            print(f"  Inserted {i} contracts...")
            
    if contract_batch:
        cursor.executemany("""
            INSERT INTO contracts (
                id, vendor_id, institution_id, sector_id, ramo_id, contract_number, title,
                contract_date, amount_inr, currency, contract_year, contract_month,
                is_direct_award, is_single_bid, is_high_value, is_year_end, is_election_year,
                risk_score, risk_level, contract_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, contract_batch)
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("=========================================================")
    print("Successfully generated Indian mock data! Database Seeded.")
    print("Run `python scripts/precompute_stats.py` to update the dashboard.")
    print("=========================================================")

if __name__ == "__main__":
    main()
