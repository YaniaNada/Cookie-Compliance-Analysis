import pandas as pd

raw_data = pd.read_excel('cookie_compliance.xlsx')

# Making a copy of the raw data to work with
df = raw_data.copy()

# Cookies classified by purpose seggregated into essential and non-essential:
essential_purposes = {'Functional', 'Service Improvement', 'Customer Support', 'Operational Efficiency', 'Legal Obligations', 'Compliance', 'Fraud Prevention', 'Security'}
non_essential_purposes = {'Analytics', 'Content Customization', 'Advertising',
                          'Tracking', 'Social Media','Personalization', 'E-commerce', 'Compliance',
                          'Performance Monitoring', 'Market Research', 'User Experience','Customer Feedback'}

# Options required in the banner for all cookies:
required_options = {'Decline All', 'Accept All', 'Customize'}

# Data collected that are considered personal data:
personal_data = {'IP Address', 'Session Data', 'Email Address', 'Phone Number', 'Payment Information',
                'Geolocation', 'Purchase History', 'Download History'}

# Key phrases to check in the cookie policy:
policy_essential = {'Types of CookiesHere are some examples of the types of cookies we use:', 'Cookie Origin'}
third_party_policy = {'Third-Party Processing'}
user_right_policy = {'What Are Your Rights'}
policy_non_essential = {'Types of CookiesHere are some examples of the types of cookies we use:', 
                        'Cookie Origin', 'Third-Party Processing', 'Consent', 'Managing Cookies'}


# 1: Cleaning up the data by removing unnecessary fields and transforming fields as necessary.
# There are no duplicates in the dataset, there are null values in 'Cookie options' however, it'll be kept as it is. 

def clean_and_transform(df):

    # Dropping irrelevant fields
    df.drop(['Cookie Name','Domain','Secure', 'HttpOnly', 'SameSite', 'Path', 'Priority', 'Partitioned','Creation Date', 'Last Accessed', 'Size (KB)', 'Host Only'], axis = 1, inplace = True)
    
    # cookies expiration period converted from seconds to years
    df['expiration (in years)'] = (((df['Expires / Max-Age (in seconds)']/60)/60)/24)/365
    return df

clean_and_transform(df) # Calling the function to clean and transform data as required


# 2: Analyzing data for compliance, defined several functions to evaluate compliance on various levels.

def analyze_cookie_compliance(df, output_filename):

    # *CHECK 1: Cookie retention compliance*

    def is_retention_compliant(df):

        # New boolean field added to the dataframe that specify whether cookie is retention compliant or not:
        df['Retention compliant'] = ((df['Duration'] == 'Session')&(df['expiration (in years)'] <1))|(
            (df['Duration'] == 'Persistent')&(df['expiration (in years)'] < 2))
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
    split_essential_and_non_essential(df)           # Classifying the cookies as essential or non-essential for further analysis
    '''-----------------------------------------------------------------------------------'''

    # *CHECK 2: Cookie banner compliance for non-essential cookies, not required for essential cookies*

    def is_banner_compliant(df):
        alist=[]
        for i in range(len(df)):      
            if (df['Essential/Non-essential'][i]== 'Non-Essential'):
                if (df['Cookie Banner'][i] == True):
                    x= df['Cookie Options'][i]
                    if required_options.issubset(x):
                        alist.append(True)
                    else:
                        alist.append(False)
                else:
                    alist.append(False)
            else:
                alist.append(True)

        df['Banner_compliant'] = alist                  # New boolean field added to the dataframe that specify whether cookie is banner compliant or not
        return df

    '''------------------------------------------------------------------------------------------'''
    def collect_data(data, i):                                                    # Function to get the data collected for each cookie
    
        for i in range(len(data)):
            words_list = (df['Data Collected '][i].split(';'))
        
        return words_list

    def is_personal_data(dataframe, collected_data, cookie_policy_set):     # Function to check if personal data is in data collected,
        for item in collected_data:                                               # if collected then checking user rights is informed in the cookie policy
            if any(item in personal_data for item in collected_data):
                if user_right_policy.issubset(cookie_policy_set):
                    return True
                return False
        return True
    
    '''-----------------------------------------------------------------------------------------'''
    # *CHECK 3: Cookie policy compliance*
 
    def is_policy_compliant(df):

        alist = []
        for i in range(len(df['Cookie Policy'])):
            cookie_policy_set = set(df['Cookie Policy'][i].split('\n'))
            y = {df['Purpose'][i]}
            collected_data = collect_data(df,i)

            # Checking essential cookies are cookie policy compliant (refer decision tree for the rules):
            if y.issubset(essential_purposes):
                if (df['Origin'][i] == 'First-party') and policy_essential.issubset(cookie_policy_set):
                    alist.append(is_personal_data(df['Origin'][i], collected_data, cookie_policy_set))
                elif (df['Origin'][i] == 'Third-party') and (df['SameParty (if cookie keeps data locally or sends it outside)'][i] == True) and (policy_essential | third_party_policy).issubset(cookie_policy_set):
                    alist.append(is_personal_data(df['Origin'][i], collected_data, cookie_policy_set | third_party_policy))
                else:
                    alist.append(False)

            # Checking non-essential cookies are cookie policy compliant (refer decision tree for the rules):
            elif y.issubset(non_essential_purposes):
                if (df['Origin'][i] == 'First-party') and policy_non_essential.issubset(cookie_policy_set):
                    alist.append(is_personal_data(df['Origin'][i], collected_data, cookie_policy_set))
                elif (df['Origin'][i] == 'Third-party') and (df['SameParty (if cookie keeps data locally or sends it outside)'][i] == True) and (policy_non_essential | third_party_policy).issubset(cookie_policy_set):
                    alist.append(is_personal_data(df['Origin'][i], collected_data, cookie_policy_set | third_party_policy))
                else:
                    alist.append(False)

        df['Policy compliant'] = alist                  # New boolean field added to the dataframe that specify whether cookie is policy compliant or not
        return df

    '''--------------------------------------------------------------------------------------'''
    
    def total_compliance_check(df):                     # Function to conduct total cookie compliance check
        
        is_retention_compliant(df)                      # Testing retention compliance
        is_banner_compliant(df)                         # Testing banner compliance
        is_policy_compliant(df)                         # Testing cookie policy compliance
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
        df['Is compliant'] = alist                      # New boolean field that finally specify whether cookie is compliant or not
        df.reset_index(inplace=True)
        return df
    '''---------------------------------------------------------------------------------------------'''
    
    # Calling all functions:
    total_compliance_check(df)                          

    # Summary of Compliance:

    compliance_summary = {
        'Overall compliance Rate (%)': (((df['Is compliant']==True).sum())/(df['Is compliant'].count())) * 100,
        'Retention compliance rate (%)': ((df['Retention compliant']==True).sum()/(df['Is compliant'].count()))*100,
        'Banner compliance rate (%)': ((df['Banner_compliant']==True).sum()/(df['Is compliant'].count()))*100,
        'Policy compliance rate (%)': ((df['Policy compliant']==True).sum()/(df['Is compliant'].count()))*100,

        '\nTotal compliant cookies': (df['Is compliant']==True).sum(),
        'Non-compliant cookies': (df['Is compliant']==False).sum(),

        '\nCompliant essential cookies': df[(df['Essential/Non-essential']=='Essential') & (df['Is compliant']==True)]['Is compliant'].count(),
        'Compliant non-essential cookies': df[(df['Essential/Non-essential']=='Non-Essential') & (df['Is compliant']==True)]['Is compliant'].count(),
        'Compliant session cookies': df[(df['Duration']=='Session')&(df['Is compliant']==True)]['Is compliant'].count(),
        'Compliant persistent cookies': df[(df['Duration']=='Persistent')&(df['Is compliant']==True)]['Is compliant'].count(),

        '\nTotal Cookies': len(df),
        'Session Cookies': (df['Duration']=='Session').sum(),
        'Persistent Cookies': (df['Duration']=='Persistent').sum(),
        'Essential Cookies': (df['Essential/Non-essential']=='Essential').sum(),
        'Non-Essential Cookies': (df['Essential/Non-essential']=='Non-Essential').sum()    
    }

    # Save the analyzed data to an excel file
    df.to_excel(output_filename, index=False)
    print(f"Analyzed data saved to {output_filename}")

    return df, compliance_summary

new_df, summary,  = analyze_cookie_compliance(df, "cookie_compliance_analysis.xlsx")


# 3: Displaying key findings post-analysis.

print("\nCompliance Summary:\n")
for key, value in summary.items():
    print(f"{key}: {value}")

print(df[(df['Essential/Non-essential']=='Non-Essential') & (df['Is compliant']==True)]['Is compliant'])