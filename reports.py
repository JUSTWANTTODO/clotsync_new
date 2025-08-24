import pandas as pd
import os
from datetime import datetime, timedelta
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load Gemini API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    google_api_key=GEMINI_API_KEY
)

def load_donor_data(csv_path="hack_data.csv"):
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    # Parse dates safely
    for col in ["created_at", "last_donated", "next_eligible"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Use latitude/longitude → city mapping (demo: Hyderabad)
    if 'latitude' in df.columns:
        df['city'] = df['latitude'].apply(lambda x: 'Hyderabad' if abs(float(x) - 17.3922792) < 0.01 else 'Other')
    else:
        df['city'] = 'Unknown'

    # Clean donation count
    if 'donation_count' in df.columns:
        df['donation_count'] = pd.to_numeric(df['donation_count'], errors='coerce').fillna(0).astype(int)
    else:
        df['donation_count'] = 0

    return df

def narrative_story(df):
    now = datetime.now()
    last_90 = now - timedelta(days=90)
    recent = df[df['last_donated'] >= last_90]

    city_stats = recent.groupby('city').agg(
        donations=('donation_count', 'sum'),
        donors=('user_id', 'nunique')
    ).sort_values('donations', ascending=False)

    summary = ""
    for city, row in city_stats.iterrows():
        summary += f"In the past 90 days, {city} had {row['donations']} donations from {row['donors']} unique donors. "

    # Find weakest city
    all_cities = df['city'].unique()
    slow_city, min_don = None, float('inf')
    for city in all_cities:
        total = recent[recent['city'] == city]['donation_count'].sum()
        if total < min_don:
            min_don, slow_city = total, city

    if slow_city:
        summary += f"⚠️ Donations in {slow_city} are the slowest — needs targeted awareness campaigns. Other is not specified here"

    return summary

def predictive_outlook(df):
    blood_stats = df.groupby('blood_group').agg(
        total_donations=('donation_count', 'sum'),
        recent_donations=('last_donated', lambda x: (x >= datetime.now() - timedelta(days=90)).sum())
    )

    summary = blood_stats.to_string()
    prompt = f"""
You are an expert blood bank analyst.
Here is a donation stats table (total vs recent 90 days):
{summary}

Today is {datetime.now().strftime('%B %Y')}.
Forecast risks for the next 3 months:
- Which blood groups risk shortage?
- Which are surplus?
- Recommend actionable campaigns (specific cities, donor segments).

Important: Do NOT use asterisks (*) or hashes (#) anywhere in your output. Use dashes (-), numbers, or plain text for lists and recommendations. Do not use Markdown formatting.

Give short, structured advice for admins.
"""
    response = llm.invoke(prompt).content.strip()
    return response

def donor_personas(df):
    now = datetime.now()
    df['days_since_last'] = (now - df['last_donated']).dt.days

    personas = []
    reg = df[(df['donation_count'] >= 3) & (df['days_since_last'] <= 120)]
    if not reg.empty:
        personas.append(f"🟢 Regular Lifesavers – donate every 90 days, dominant blood group: {reg['blood_group'].mode()[0]}")
    emer = df[(df['donation_count'] <= 2) & (df['days_since_last'] <= 180)]
    if not emer.empty:
        personas.append(f"🟡 Emergency Helpers – donate on request, mostly {emer['blood_group'].mode()[0]}")
    first = df[(df['donation_count'] == 1) & (df['last_donated'] >= now - timedelta(days=365))]
    if not first.empty:
        personas.append(f"🔵 First Timers – donated once in the past year, need encouragement & retention")

    return '\n'.join(personas)

def impact_simulation(df):
    total_donors = df['user_id'].nunique()
    extra_lives = total_donors * 3
    return f"If every donor gave just one more time this year → {extra_lives:,} extra lives could be saved."

def anomaly_risk(df):
    now = datetime.now()
    two_years_ago = now - timedelta(days=730)
    city = 'Hyderabad'
    city_df = df[df['city'].str.lower() == city.lower()]

    if not city_df.empty:
        low_freq = city_df[(city_df['last_donated'] < two_years_ago) | (city_df['donation_count'] < 1)]
        pct = 100 * len(low_freq) / len(city_df)
        if pct > 0:
            return f"⚠️ {pct:.0f}% of donors in {city} donated <1 time in past 2 years — dropout risk. Need re-engagement calls."
    return "✅ No major anomalies detected."

def generate_ai_report(csv_path="donors.csv"):
    df = load_donor_data(csv_path)
    report = {
        'narrative': narrative_story(df),
        'predictive_outlook': predictive_outlook(df),
        'personas': donor_personas(df),
        'impact_simulation': impact_simulation(df),
        'anomaly_risk': anomaly_risk(df)
    }
    return report

def donor_leaderboard(df, top_n=20):
    # Define leaderboard tiers
    tiers = [
        (500, 100, "🕊️ Eternal Lifesaver", "Lifetime achievement tier"),
        (300, 60, "👑 Blood Legend", "Inspirational donor, community leader"),
        (200, 40, "🌟 Hero of Thalassemia", "Long-term commitment"),
        (100, 20, "🔥 Life Champion", "Regular donor making real impact"),
        (50, 10, "🛡️ Guardian of Hope", "Trusted donor for Thalassemia"),
        (25, 5, "💖 Hope Giver", "Consistently helping patients"),
        (5, 1, "🌱 Life Spark", "First step towards saving lives"),
        (0, 0, "", "Baby step")
    ]

    def get_tier(donations):
        for points, min_don, badge, title in tiers:
            if donations >= min_don:
                return points, badge, title
        return 0, "", "Baby step"

    # Assume df has columns: user_id, name, donation_count
    leaderboard = []
    for _, row in df.iterrows():
        name = row.get('name', f"User {row.get('user_id', '')}")
        donations = row.get('donation_count', 0)
        points, badge, title = get_tier(donations)
        leaderboard.append({
            'user_id': row.get('user_id', ''),
            'name': name,
            'donations': donations,
            'points': points,
            'badge': badge,
            'title': title
        })
    # Sort by donations desc, then name
    leaderboard = sorted(leaderboard, key=lambda x: (-x['donations'], x['name']))
    return leaderboard[:top_n]

def debug_data_structure(df):
    """Debug function to understand data structure"""
    try:
        print(f"DataFrame length: {len(df)}")
        if len(df) > 0:
            print(f"First row keys: {list(df.data[0].keys())}")
            print(f"Sample row: {df.data[0]}")
            
            # Check data types
            for key, value in df.data[0].items():
                print(f"{key}: {type(value)} = {value}")
                
            # Check for None values
            none_count = sum(1 for row in df for value in row.values() if value is None)
            print(f"Total None values: {none_count}")
            
    except Exception as e:
        print(f"Debug error: {e}")

# Database-based report generation
def generate_ai_report_from_db():
    """Generate AI report from database instead of CSV"""
    try:
        # Import database models
        from models import Donor, Hospital, Patient, BloodRequest
        from extensions import db
        
        print("Starting report generation...")
        
        # Get current data from database
        donors = Donor.query.all()
        hospitals = Hospital.query.all()
        patients = Patient.query.all()
        blood_requests = BloodRequest.query.all()
        
        print(f"Found {len(donors)} donors, {len(hospitals)} hospitals, {len(patients)} patients, {len(blood_requests)} blood requests")
        
        # Convert to DataFrame-like structure for compatibility
        donor_data = []
        for donor in donors:
            donor_data.append({
                'user_id': donor.id,
                'name': donor.name,
                'blood_group': donor.blood_group,
                'location': donor.location,
                'donation_count': donor.donations_count,
                'last_donated': donor.last_donated,
                'next_eligible': donor.next_eligible,
                'eligibility_status': donor.eligibility_status,
                'gender': donor.gender,
                'created_at': donor.created_at
            })
        
        print(f"Processed {len(donor_data)} donor records")
        
        # Create a simple DataFrame-like structure
        class SimpleDF:
            def __init__(self, data):
                self.data = data
                self.columns = data[0].keys() if data else []
            
            def __iter__(self):
                return iter(self.data)
            
            def __getitem__(self, key):
                if isinstance(key, str):
                    return [row.get(key) for row in self.data]
                return self.data[key]
            
            def groupby(self, key):
                groups = {}
                for row in self.data:
                    group_key = row.get(key)
                    if group_key not in groups:
                        groups[group_key] = []
                    groups[group_key].append(row)
                return SimpleGroupBy(groups)
            
            def __len__(self):
                return len(self.data)
            
            def empty(self):
                return len(self.data) == 0
            
            def mode(self):
                if not self.data:
                    return []
                # Simple mode calculation
                values = [row.get('blood_group') for row in self.data if row.get('blood_group')]
                if not values:
                    return []
                from collections import Counter
                counter = Counter(values)
                max_count = max(counter.values())
                return [k for k, v in counter.items() if v == max_count]
        
        class SimpleGroupBy:
            def __init__(self, groups):
                self.groups = groups
            
            def agg(self, **kwargs):
                result = {}
                for group_key, group_data in self.groups.items():
                    result[group_key] = {}
                    for agg_name, agg_func in kwargs.items():
                        if isinstance(agg_func, tuple):
                            col, func = agg_func
                            if func == 'sum':
                                result[group_key][agg_name] = sum(row.get(col, 0) for row in group_data)
                            elif func == 'nunique':
                                result[group_key][agg_name] = len(set(row.get(col) for row in group_data))
                        else:
                            # Handle lambda functions
                            if 'last_donated' in str(agg_func):
                                # Count recent donations
                                now = datetime.now()
                                recent = [row for row in group_data if row.get('last_donated') and row['last_donated'] >= now - timedelta(days=90)]
                                result[group_key][agg_name] = len(recent)
                return result
        
        # Create DataFrame-like object
        df = SimpleDF(donor_data)
        
        # Debug the data structure
        debug_data_structure(df)
        
        # Generate report sections with error handling
        try:
            narrative = narrative_story_db(df)
            print(f"Narrative generated successfully: {len(narrative)} characters")
        except Exception as e:
            print(f"Narrative error: {e}")
            narrative = "Error generating narrative story."
        
        try:
            predictive = predictive_outlook_db(df)
            print(f"Predictive generated successfully: {len(predictive)} characters")
        except Exception as e:
            print(f"Predictive error: {e}")
            predictive = "Error generating predictive outlook."
        
        try:
            personas = donor_personas_db(df)
            print(f"Personas generated successfully: {len(personas)} characters")
        except Exception as e:
            print(f"Personas error: {e}")
            personas = "Error generating donor personas."
        
        try:
            impact = impact_simulation_db(df)
            print(f"Impact generated successfully: {len(impact)} characters")
        except Exception as e:
            print(f"Impact error: {e}")
            impact = "Error generating impact simulation."
        
        try:
            anomaly = anomaly_risk_db(df)
            print(f"Anomaly generated successfully: {len(anomaly)} characters")
        except Exception as e:
            print(f"Anomaly error: {e}")
            anomaly = "Error generating anomaly and risk detection."
        
        report = {
            'narrative': narrative,
            'predictive_outlook': predictive,
            'personas': personas,
            'impact_simulation': impact,
            'anomaly_risk': anomaly
        }
        
        print("Report generation completed successfully")
        return report
        
    except Exception as e:
        print(f"Database report generation error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'narrative': 'Error generating report from database.',
            'predictive_outlook': 'Database report generation failed.',
            'personas': 'Unable to load donor personas from database.',
            'impact_simulation': 'Database impact simulation unavailable.',
            'anomaly_risk': 'Database risk detection failed.'
        }

def narrative_story_db(df):
    """Generate narrative story from database data"""
    try:
        if len(df) == 0:
            return "No donor data available for narrative analysis."
        
        now = datetime.now()
        last_90 = now - timedelta(days=90)
        
        # Count recent donations
        recent_donors = 0
        total_donations = 0
        
        for row in df:
            last_donated = row.get('last_donated')
            if last_donated:
                # Handle both datetime and date objects
                if hasattr(last_donated, 'date'):
                    last_donated = last_donated.date()
                elif isinstance(last_donated, str):
                    try:
                        last_donated = datetime.strptime(last_donated, '%Y-%m-%d').date()
                    except:
                        continue
                
                if isinstance(last_donated, datetime.date) and last_donated >= last_90.date():
                    recent_donors += 1
                    total_donations += row.get('donation_count', 0)
        
        # Get location statistics
        locations = {}
        for row in df:
            loc = row.get('location', 'Unknown')
            if loc not in locations:
                locations[loc] = {'donors': 0, 'donations': 0}
            locations[loc]['donors'] += 1
            locations[loc]['donations'] += row.get('donation_count', 0)
        
        # Find most active location
        most_active = max(locations.items(), key=lambda x: x[1]['donations']) if locations else None
        
        summary = f"In the past 90 days, {recent_donors} donors made {total_donations} donations. "
        
        if most_active:
            summary += f"The most active location is {most_active[0]} with {most_active[1]['donations']} donations from {most_active[1]['donors']} donors. "
        
        # Find areas needing attention
        low_activity = [(loc, data) for loc, data in locations.items() if data['donations'] < 5]
        if low_activity:
            summary += f"⚠️ Areas needing attention: {', '.join([loc for loc, _ in low_activity[:3]])} - consider targeted awareness campaigns."
        
        return summary
        
    except Exception as e:
        print(f"Narrative story error: {e}")
        import traceback
        traceback.print_exc()
        return "Unable to generate narrative story from database data."

def predictive_outlook_db(df):
    """Generate predictive outlook from database data"""
    try:
        if len(df) == 0:
            return "No donor data available for predictive analysis."
        
        # Analyze blood group distribution
        blood_groups = {}
        for row in df:
            bg = row.get('blood_group', 'Unknown')
            if bg not in blood_groups:
                blood_groups[bg] = {'total': 0, 'recent': 0}
            blood_groups[bg]['total'] += row.get('donation_count', 0)

            # Check recent donations
            last_donated = row.get('last_donated')
            parsed_date = None
            if last_donated:
                # Handle datetime, date, and string formats
                if isinstance(last_donated, datetime):
                    parsed_date = last_donated.date()
                elif isinstance(last_donated, str):
                    # Try multiple formats
                    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y'):
                        try:
                            parsed_date = datetime.strptime(last_donated, fmt).date()
                            break
                        except Exception:
                            continue
                elif hasattr(last_donated, 'date'):
                    try:
                        parsed_date = last_donated.date()
                    except Exception:
                        pass

            if parsed_date and parsed_date >= datetime.now().date() - timedelta(days=90):
                blood_groups[bg]['recent'] += 1
        
        # Generate forecast
        forecast = "Blood Group Analysis & 3-Month Forecast:\n\n"
        
        for bg, stats in blood_groups.items():
            if stats['total'] > 0:
                recent_ratio = stats['recent'] / stats['total'] if stats['total'] > 0 else 0
                if recent_ratio < 0.3:
                    forecast += f"- {bg}: RISK of shortage (low recent activity)\n"
                elif recent_ratio > 0.7:
                    forecast += f"- {bg}: SURPLUS likely (high recent activity)\n"
                else:
                    forecast += f"- {bg}: STABLE supply\n"
        
        forecast += "\nRecommendations:\n"
        forecast += "- Focus on O- and A+ donors (most needed)\n"
        forecast += "- Re-engage donors who haven't donated in 6+ months\n"
        forecast += "- Launch awareness campaigns in low-activity areas\n"
        
        return forecast
        
    except Exception as e:
        print(f"Predictive outlook error: {e}")
        import traceback
        traceback.print_exc()
        return "Unable to generate predictive outlook from database data."

def donor_personas_db(df):
    """Generate donor personas from database data"""
    try:
        if len(df) == 0:
            return "No donor data available for persona analysis."
        
        now = datetime.now()
        personas = []
        
        # Calculate donor categories
        regular_donors = 0
        emergency_donors = 0
        first_timers = 0
        
        for row in df:
            donations = row.get('donation_count', 0)
            last_donation = row.get('last_donated')
            
            if last_donation:
                # Handle both datetime and date objects
                if hasattr(last_donation, 'date'):
                    last_donation = last_donation.date()
                elif isinstance(last_donation, str):
                    try:
                        last_donation = datetime.strptime(last_donation, '%Y-%m-%d').date()
                    except:
                        continue
                
                if isinstance(last_donation, datetime.date):
                    days_since = (now.date() - last_donation).days
                    
                    if donations >= 3 and days_since <= 120:
                        regular_donors += 1
                    elif donations <= 2 and days_since <= 180:
                        emergency_donors += 1
                    elif donations == 1 and days_since <= 365:
                        first_timers += 1
        
        # Get dominant blood group
        blood_groups = [row.get('blood_group') for row in df if row.get('blood_group')]
        if blood_groups:
            from collections import Counter
            dominant_bg = Counter(blood_groups).most_common(1)[0][0]
        else:
            dominant_bg = "Unknown"
        
        if regular_donors > 0:
            personas.append(f"🟢 Regular Lifesavers ({regular_donors} donors) - donate every 90 days, dominant blood group: {dominant_bg}")
        
        if emergency_donors > 0:
            personas.append(f"🟡 Emergency Helpers ({emergency_donors} donors) - donate on request, mostly {dominant_bg}")
        
        if first_timers > 0:
            personas.append(f"🔵 First Timers ({first_timers} donors) - donated once in the past year, need encouragement & retention")
        
        if not personas:
            personas.append("No donor personas identified from current data.")
        
        return '\n'.join(personas)
        
    except Exception as e:
        print(f"Donor personas error: {e}")
        import traceback
        traceback.print_exc()
        return "Unable to generate donor personas from database data."

def impact_simulation_db(df):
    """Generate impact simulation from database data"""
    try:
        if len(df) == 0:
            return "No donor data available for impact simulation."
        
        total_donors = len(df)
        total_donations = sum(row.get('donation_count', 0) for row in df)
        
        if total_donors > 0:
            avg_donations = total_donations / total_donors
            potential_extra = total_donors * 3  # If each donor gave 3 more times
            
            return f"Current Impact: {total_donors} donors have made {total_donations} total donations (avg: {avg_donations:.1f} per donor).\n\nPotential Impact: If every donor gave just 3 more times this year → {potential_extra:,} extra lives could be saved!"
        else:
            return "No donor data available for impact simulation."
            
    except Exception as e:
        print(f"Impact simulation error: {e}")
        return "Unable to generate impact simulation from database data."

def anomaly_risk_db(df):
    """Generate anomaly and risk detection from database data"""
    try:
        if len(df) == 0:
            return "No donor data available for risk analysis."
        
        now = datetime.now()
        two_years_ago = now - timedelta(days=730)
        
        # Analyze risks
        risks = []
        
        # Check for inactive donors
        inactive_donors = 0
        for row in df:
            last_donated = row.get('last_donated')
            if last_donated:
                # Handle both datetime and date objects
                if hasattr(last_donated, 'date'):
                    last_donated = last_donated.date()
                elif isinstance(last_donated, str):
                    try:
                        last_donated = datetime.strptime(last_donated, '%Y-%m-%d').date()
                    except:
                        continue
                
                if isinstance(last_donated, datetime.date) and last_donated < two_years_ago.date():
                    inactive_donors += 1
        
        if inactive_donors > 0:
            inactive_pct = (inactive_donors / len(df)) * 100
            risks.append(f"⚠️ {inactive_pct:.0f}% of donors haven't donated in 2+ years — dropout risk")
        
        # Check eligibility status
        ineligible_donors = sum(1 for row in df if row.get('eligibility_status') == 'not eligible')
        if ineligible_donors > 0:
            ineligible_pct = (ineligible_donors / len(df)) * 100
            risks.append(f"⚠️ {ineligible_pct:.0f}% of donors are currently ineligible — need re-engagement")
        
        # Check for low donation counts
        low_donors = sum(1 for row in df if row.get('donation_count', 0) < 2)
        if low_donors > 0:
            low_pct = (low_donors / len(df)) * 100
            risks.append(f"⚠️ {low_pct:.0f}% of donors have less than 2 donations — retention needed")
        
        if not risks:
            return "✅ No major anomalies detected. Donor base appears healthy."
        else:
            return "Risk Analysis:\n" + "\n".join(risks)
            
    except Exception as e:
        print(f"Anomaly risk error: {e}")
        import traceback
        traceback.print_exc()
        return "Unable to generate anomaly and risk detection from database data."

if __name__ == "__main__":
    rep = generate_ai_report()
    for k, v in rep.items():
        print(f"\n=== {k.upper()} ===\n{v}\n")