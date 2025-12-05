#!/usr/bin/env python3
"""
Test script to verify all decision-related endpoints work correctly.
Run this after the database migration to ensure everything is functional.
"""

import requests
from uuid import uuid4
import json

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    except:
        print(f"Response: {response.text}")

def test_decision_workflow():
    """Test complete decision workflow."""
    
    # Step 1: Create users and pool
    user1_id = str(uuid4())
    user2_id = str(uuid4())
    
    print(f"\n🧪 Testing Decision Endpoints")
    print(f"User 1 ID: {user1_id}")
    print(f"User 2 ID: {user2_id}")
    
    # Step 2: Add users to pool
    print("\n📍 Step 1: Adding users to pool...")
    
    for user_id in [user1_id, user2_id]:
        response = requests.post(
            f"{BASE_URL}/users/{user_id}/pool",
            json={
                "location": "San Francisco",
                "coord_x": 37.7749,
                "coord_y": -122.4194
            }
        )
        print_response(f"Add user {user_id[:8]}... to pool", response)
        if response.status_code != 201:
            print("❌ Failed to add user to pool")
            return False
    
    # Step 3: Generate matches
    print("\n🎲 Step 2: Generating matches...")
    response = requests.post(f"{BASE_URL}/users/{user1_id}/matches")
    print_response("Generate matches", response)
    
    if response.status_code != 201:
        print("❌ Failed to generate matches")
        return False
    
    matches = response.json().get("matches", [])
    if not matches:
        print("❌ No matches created")
        return False
    
    match_id = matches[0]["match_id"]
    print(f"\n✅ Match created: {match_id}")
    
    # Step 4: Submit decision from user1 (via composite endpoint)
    print("\n✅ Step 3: User 1 accepts match...")
    response = requests.post(
        f"{BASE_URL}/users/{user1_id}/matches/{match_id}/decisions",
        json={"decision": "accept"}
    )
    print_response(f"User 1 decision (composite endpoint)", response)
    
    if response.status_code not in [200, 201]:
        print("❌ Failed to submit user 1 decision")
        return False
    
    # Step 5: Check match status (should still be waiting)
    print("\n🔍 Step 4: Checking match status after one accept...")
    response = requests.get(f"{BASE_URL}/matches/{match_id}")
    print_response("Get match status", response)
    
    if response.status_code != 200:
        print("❌ Failed to get match")
        return False
    
    match_data = response.json()
    if match_data["status"] != "waiting":
        print(f"⚠️  Expected 'waiting', got '{match_data['status']}'")
    else:
        print("✅ Match status is 'waiting' (correct)")
    
    # Step 6: Submit decision from user2 (via direct endpoint)
    print("\n✅ Step 5: User 2 accepts match...")
    response = requests.post(
        f"{BASE_URL}/matches/{match_id}/decisions",
        json={
            "match_id": match_id,
            "user_id": user2_id,
            "decision": "accept"
        }
    )
    print_response(f"User 2 decision (direct endpoint)", response)
    
    if response.status_code not in [200, 201]:
        print("❌ Failed to submit user 2 decision")
        return False
    
    # Step 7: Check match status (should now be accepted)
    print("\n🔍 Step 6: Checking match status after both accept...")
    response = requests.get(f"{BASE_URL}/matches/{match_id}")
    print_response("Get match status", response)
    
    if response.status_code != 200:
        print("❌ Failed to get match")
        return False
    
    match_data = response.json()
    if match_data["status"] != "accepted":
        print(f"❌ Expected 'accepted', got '{match_data['status']}'")
        return False
    else:
        print("✅ Match status is 'accepted' (correct)")
    
    # Step 8: List decisions for the match
    print("\n📋 Step 7: Listing all decisions for match...")
    response = requests.get(f"{BASE_URL}/matches/{match_id}/decisions")
    print_response("List match decisions", response)
    
    if response.status_code != 200:
        print("❌ Failed to list decisions")
        return False
    
    decisions = response.json()
    if len(decisions) != 2:
        print(f"❌ Expected 2 decisions, got {len(decisions)}")
        return False
    else:
        print(f"✅ Found {len(decisions)} decisions")
    
    # Step 9: Get user decisions
    print("\n📋 Step 8: Getting decisions for user 1...")
    response = requests.get(f"{BASE_URL}/users/{user1_id}/decisions")
    print_response("Get user decisions", response)
    
    if response.status_code != 200:
        print("❌ Failed to get user decisions")
        return False
    
    user_decisions = response.json()
    print(f"✅ User has {user_decisions['decisions_count']} decision(s)")
    
    # Step 10: Test reject workflow
    print("\n🔄 Step 9: Testing reject workflow...")
    
    # Generate another match
    response = requests.post(f"{BASE_URL}/users/{user1_id}/matches")
    matches = response.json().get("matches", [])
    
    if matches:
        match_id_2 = matches[0]["match_id"]
        print(f"Created second match: {match_id_2}")
        
        # User 1 rejects
        response = requests.post(
            f"{BASE_URL}/matches/{match_id_2}/decisions",
            json={
                "match_id": match_id_2,
                "user_id": user1_id,
                "decision": "reject"
            }
        )
        print_response("User 1 rejects", response)
        
        # Check status
        response = requests.get(f"{BASE_URL}/matches/{match_id_2}")
        match_data = response.json()
        
        if match_data["status"] != "rejected":
            print(f"❌ Expected 'rejected', got '{match_data['status']}'")
            return False
        else:
            print("✅ Match status is 'rejected' (correct - one reject is enough)")
    
    print("\n" + "="*60)
    print("🎉 ALL DECISION ENDPOINT TESTS PASSED!")
    print("="*60)
    return True

if __name__ == "__main__":
    try:
        success = test_decision_workflow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
