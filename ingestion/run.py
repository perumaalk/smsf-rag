import os
from ingestion.parsers.sis_parser import get_sis_nodes
from ingestion.parsers.ato_parser import get_ato_nodes
from ingestion.pipeline import build_pipeline

def main():
    all_nodes = []
    
    print("🚀 Starting Ingestion...")

    # 1. Process SIS Act
    sis_path = "data/source/sis_act.pdf"
    if os.path.exists(sis_path):
        print("Parsing SIS Act...")
        all_nodes.extend(get_sis_nodes(sis_path))

    # 2. Process ATO Rulings
    ato_dir = "data/source/ato_rulings/"
    for file in os.listdir(ato_dir):
        if file.endswith(".pdf"):
            print(f"Parsing Ruling: {file}...")
            all_nodes.extend(get_ato_nodes(os.path.join(ato_dir, file)))

    # 3. PRIVATE DATA (Individual Deeds)
    # In production, you might loop through a DB of funds
    funds_to_ingest = [
        {"id": "FUND_ALPHA_001", "path": "data/source/deeds/alpha_deed_scanned.pdf"},
        {"id": "FUND_BETA_999", "path": "data/source/deeds/beta_deed_v2.pdf"}
    ]

    for fund in funds_to_ingest:
        print(f"Parsing Private Deed for {fund['id']}...")
        deed_nodes = get_trust_deed_nodes(fund['path'], fund['id'])
        all_nodes.extend(deed_nodes)

    # 4. Finalize
    if all_nodes:
        build_pipeline(all_nodes)
        print(f"✅ Successfully indexed {len(all_nodes)} nodes to Qdrant.")
    else:
        print("❌ No documents found to index.")

if __name__ == "__main__":
    main()