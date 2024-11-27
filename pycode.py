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


'''Analyze data for compliance'''

def analyze_cookie_compliance(df, output_filename):

    # Check 1: Cookie retention compliance

    def is_retention_compliant(df):
        df['Retention compliant'] = ((df['Duration'] == 'Session')&(df['expiration (in years)'] <1))|((df['Duration'] == 'Persistent')&(df['expiration (in years)'] < 2))
        return df

    ''' ---------------------------------------------------------------------------------------'''
    # Split into essential and non-essential based on purpose

    def split_essential_and_non_essential(df):
        essential_purposes = {'Functional', 'Operational Efficiency', 'Legal Obligations', 'Compliance', 'Fraud Prevention', 'Security'}
        non_essential_purposes = {'Analytics', 'Service Improvement',
        'Content Customization', 'Advertising', 'Customer Support',
        'Tracking', 'Social Media','Personalization', 'E-commerce', 'Compliance',
        'Performance Monitoring', 'Market Research', 'User Experience',
        'Customer Feedback'}

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
        # Key options required in the banner
        required_options = {'Decline All', 'Accept All', 'Customize'}
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

    def is_policy_compliant(df): 
        # Key phrases to check for policy compliance
        policy_essential = {'Types of CookiesHere are some examples of the types of cookies we use:', 'Cookie Origin'}
        policy_third_party = {'Third-Party Processing'}
        policy_non_essential = {'Types of CookiesHere are some examples of the types of cookies we use:', 'Cookie Origin', 'Third-Party Processing', 'Consent','Managing Cookies', 'What Are Your Rights'}

        alist = []
        for i in range(len(df['Cookie Policy'])):
            x = {df['Cookie Policy'][i]}
            x= df['Cookie Policy'].str.split('\n')[i] 
            
            if df['Essential/Non-essential'][i]=='Essential':
                if (df['Origin'][i] == 'First-party')&(policy_essential.issubset(x)):
                    alist.append(True)
                elif (df['Origin'][i] == 'Third-party')&((policy_essential & policy_third_party).issubset(x)):
                    alist.append(True)
                else:
                    alist.append(False)

            elif df['Essential/Non-essential'][i]=='Non-Essential':
                if (df['Origin'][i] == 'First-party')&(policy_non_essential.issubset(x)):
                    alist.append(True)
                elif (df['Origin'][i] == 'Third-party')&((policy_non_essential & policy_third_party).issubset(x)):
                    alist.append(True)
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
    df.to_excel(output_filename, index=False)
    print(f"Analyzed data saved to {output_filename}")

    return df, compliance_summary

compliant_df, summary,  = analyze_cookie_compliance(df, "cookie_compliance_analysis.xlsx")

# Display results
print("\nCompliance Summary:")
for key, value in summary.items():
    print(f"{key}: {value}")