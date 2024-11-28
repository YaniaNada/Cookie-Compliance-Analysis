import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

raw_data = pd.read_excel('cookie_compliance.xlsx')

# Making a copy of the raw data to work with
df = raw_data.copy()

'''Clean and transform'''
def clean_and_transform(df):
    # Dropping irrelevant fields
    df.drop(['Cookie Name','Domain','Secure', 'HttpOnly', 'SameSite', 'Path', 'Priority', 'Partitioned','Creation Date', 'Last Accessed', 'Size (KB)', 'Host Only'], axis = 1, inplace = True)
    
    # cookies expiration period converted from seconds to years
    df['expiration (in years)'] = (((df['Expires / Max-Age (in seconds)']/60)/60)/24)/365

    return df

clean_and_transform(df)

essential_purposes = {'Functional', 'Service Improvement', 'Customer Support', 'Operational Efficiency', 'Legal Obligations', 'Compliance', 'Fraud Prevention', 'Security'}
non_essential_purposes = {'Analytics', 'Content Customization', 'Advertising',
                          'Tracking', 'Social Media','Personalization', 'E-commerce', 'Compliance',
                          'Performance Monitoring', 'Market Research', 'User Experience','Customer Feedback'}

# Key options required in the banner
required_options = {'Decline All', 'Accept All', 'Customize'}

# Key phrases to check for policy compliance
personal_data = {'IP Address', 'Session Data', 'Email Address', 'Phone Number', 'Payment Information',
                'Geolocation', 'Purchase History', 'Download History'}
cpolicy_essential = {'Types of CookiesHere are some examples of the types of cookies we use:', 'Cookie Origin'}
third_party_policy = {'Third-Party Processing'}
cpolicy_non_essential = {'Types of CookiesHere are some examples of the types of cookies we use:', 
                        'Cookie Origin', 'Third-Party Processing', 'Consent', 'Managing Cookies'}
user_right_policy = {'What Are Your Rights'}

'''Analyze data for compliance'''

def analyze_cookie_compliance(df, output_filename):

    # Check 1: Cookie retention compliance

    def is_retention_compliant(df):
        df['Retention compliant'] = ((df['Duration'] == 'Session')&(df['expiration (in years)'] <1))|((df['Duration'] == 'Persistent')&(df['expiration (in years)'] < 2))
        return df

    ''' ---------------------------------------------------------------------------------------'''
    # Split into essential and non-essential based on purpose

    def split_essential_and_non_essential(df):
        alist = []
        for i in range(len(df)):       
            if df['Purpose'][i] in essential_purposes:
                alist.append('Essential')
                
            else:
                alist.append('Non-Essential')
        df['Essential/Non-essential'] = alist
        return df
    
    '''-----------------------------------------------------------------------------------'''

    # Check 2: Cookie banner compliance for non-essential cookies

    def is_banner_compliant(df):
        alist=[]
        for i in range(len(df)):      
            if (df['Essential/Non-essential'][i]== 'Non-Essential')&(df['Cookie Banner'][i] == True):
                x= df['Cookie Options'][i]
                if required_options.issubset(x):
                    alist.append(True)
                else:
                    alist.append(False)
            else:
                alist.append(True)

        df['Banner_compliant'] = alist
        return df

    '''------------------------------------------------------------------------------------------'''
    # Check 3: Cookie policy compliance
    from nltk import ngrams
    def get_data_collected(data):
        n=1
        words = []
        for i in range(len(data)):
            unigrams = ngrams(data['Data Collected '][i].split(';'), n)

            for grams in unigrams:
                words.append(grams)

        return words
    
    def collect_data(n):
        data = df[n:n+1]
        data.reset_index(inplace=True)
        cust_fb_data = get_data_collected(data)
        flattened = [item.strip() for sublist in cust_fb_data for item in sublist]
        var = pd.Series(flattened).unique()

        return var
    
    def is_policy_compliant(df):
        alist = []

        # Function to evaluate conditions
        def evaluate_policy(origin, collected_data, x, policy_set):
            for item in collected_data:
                if any(personal_item in personal_data for personal_item in collected_data):
                    if user_right_policy.issubset(x):
                        return True
                    return False
            return True

        # Iterate through the DataFrame rows
        for i in range(len(df['Cookie Policy'])):
            x = set(df['Cookie Policy'][i].split('\n'))  # Convert to a set for subset checking
            y = {df['Purpose'][i]}  # Purpose as a set
            collected_data = collect_data(i)

            # Check for essential cookies
            if y.issubset(essential_purposes):
                if (df['Origin'][i] == 'First-party') and cpolicy_essential.issubset(x):
                    alist.append(evaluate_policy(df['Origin'][i], collected_data, x, cpolicy_essential))
                elif (df['Origin'][i] == 'Third-party') and (df['SameParty (if cookie keeps data locally or sends it outside)'][i] == True) and (cpolicy_essential | third_party_policy).issubset(x):
                    alist.append(evaluate_policy(df['Origin'][i], collected_data, x, cpolicy_essential | third_party_policy))
                else:
                    alist.append(False)

            # Check for non-essential cookies
            elif y.issubset(non_essential_purposes):
                if (df['Origin'][i] == 'First-party') and cpolicy_non_essential.issubset(x):
                    alist.append(evaluate_policy(df['Origin'][i], collected_data, x, cpolicy_non_essential))
                elif (df['Origin'][i] == 'Third-party') and (df['SameParty (if cookie keeps data locally or sends it outside)'][i] == True) and (cpolicy_non_essential | third_party_policy).issubset(x):
                    alist.append(evaluate_policy(df['Origin'][i], collected_data, x, cpolicy_non_essential | third_party_policy))
                else:
                    alist.append(False)

        df['Policy compliant'] = alist
        return df

    '''--------------------------------------------------------------------------------------'''
    # Final Compliance Check

    def total_compliance_check(df):
        is_retention_compliant(df)
        split_essential_and_non_essential(df)
        is_banner_compliant(df)
        is_policy_compliant(df)
        alist=[]
        for i in range(len(df)):
            if df['Retention compliant'][i]==True:
                if df['Banner_compliant'][i]==True:
                    if df['Policy compliant'][i]==True:
                        alist.append(True)
                    else:
                        alist.append(False)
                else:
                    alist.append(False)
            else:
                alist.append(False)
        df['Is compliant'] = alist
        return df
    '''---------------------------------------------------------------------------------------------'''
    
    total_compliance_check(df)
    # Summary of Compliance
    compliance_summary = {
        'Total Cookies': len(df),
        'Session Cookies': (df['Duration']=='Session').sum(),
        'Persistent Cookies': (df['Duration']=='Persistent').sum(),
        'Essential Cookies': (df['Essential/Non-essential']=='Essential').sum(),
        'Non-Essential Cookies': (df['Essential/Non-essential']=='Non-Essential').sum(),
        'Compliant Cookies': (df['Is compliant']==True).sum(),
        'Non-Compliant Cookies': (df['Is compliant']==False).sum(),
        'Compliance Rate (%)': (((df['Is compliant']==True).sum())/(df['Is compliant'].count())) * 100
    }

    # Detailed breakdown of non-compliance reasons
    non_compliant_cookies = df[df['Is compliant'] == False]

    # Save the analyzed data to a CSV file
    df.to_csv(output_filename, index=False)
    print(f"Analyzed data saved to {output_filename}")

    return df, compliance_summary

compliant_df, summary,  = analyze_cookie_compliance(df, "cookie_compliance_analysis.csv")

# Display results
print("\nCompliance Summary:")
for key, value in summary.items():
    print(f"{key}: {value}")