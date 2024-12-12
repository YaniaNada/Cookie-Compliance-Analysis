# Importing pandas library for data manipulation and analysis
import pandas as pd

# Reading raw data from an Excel file
raw_data = pd.read_excel('cookie_compliance_data.xlsx')

# Making a copy of the raw data to work with
df = raw_data.copy()

# Defining cookie purposes considered essential
essential_purposes = {'Functional', 'Service Improvement', 'Customer Support', 'Operational Efficiency', 
                      'Legal Obligations', 'Compliance', 'Fraud Prevention', 'Security'}

# Defining cookie purposes considered non-essential
non_essential_purposes = {'Analytics', 'Content Customization', 'Advertising',
                          'Tracking', 'Social Media','Personalization', 'E-commerce', 'Compliance',
                          'Performance Monitoring', 'Market Research', 'User Experience','Customer Feedback'}

# Defining data types considered personal data
personal_data = ['IP Address', 'Session Data', 'Email Address', 'Phone Number', 'Payment Information',
                'Geolocation', 'Purchase History', 'Download History']

# Key phrases for policy compliance checks for essential cookies
policy_essential = {'Types of CookiesHere are some examples of the types of cookies we use:', 'Cookie Origin'}

# Key phrases for policy compliance checks for third-party cookie origins
third_party_policy = {'Third-Party Processing'}

# Key phrases for policy compliance checks for personal data collection
user_right_policy = {'What Are Your Rights'}

# Key phrases for policy compliance checks for non-essential cookies
policy_non_essential = {'Types of CookiesHere are some examples of the types of cookies we use:', 
                        'Cookie Origin', 'Consent', 'Managing Cookies'}


# Cleaning and transforming the data by removing unnecessary fields and modifying fields as needed.
# There are no duplicates in the dataset, there are null values in 'Cookie options' however, it'll be kept as it is. 
def clean_and_transform(df):

    # Dropping irrelevant fields
    df.drop(['Cookie Name','Domain','Secure', 'HttpOnly', 'SameSite', 'Path', 'Priority', 
             'Partitioned','Creation Date', 'Last Accessed', 'Size (KB)', 'Host Only'], axis = 1, inplace = True)
    
    # Converting cookie expiration period from seconds to years
    df['expiration (in years)'] = (((df['Expires / Max-Age (in seconds)']/60)/60)/24)/365
    return df

# Cleaning and transforming the dataset
clean_and_transform(df)

# Analyzing data for compliance by defining several compliance evaluation functions
def analyze_cookie_compliance(df, output_filename):

    # Check 1: Evaluating cookie retention compliance

    def is_retention_compliant(df):

        # Adding a boolean field to specify retention compliance
        df['Retention compliant'] = ((df['Duration'] == 'Session')&(df['expiration (in years)'] <0.02))|(
            (df['Duration'] == 'Persistent')&(df['expiration (in years)'] < 2))
        
        return df

    ''' ---------------------------------------------------------------------------------------'''
    
    # Classifying cookies as essential or non-essential
    def split_essential_and_non_essential(df):
        alist = []
        for i in range(len(df)):       

            if df['Purpose'][i] in essential_purposes:
                alist.append('Essential')
                
            else:
                alist.append('Non-Essential')

        df['Essential/Non-essential'] = alist
        return df
    split_essential_and_non_essential(df)           
    '''-----------------------------------------------------------------------------------'''

    # Check 2: Evaluating cookie banner compliance for non-essential cookies

    def is_banner_compliant(df):
        alist=[]
        for i in range(len(df)):      

            if (df['Essential/Non-essential'][i]== 'Non-Essential'):

                if (df['Cookie Banner'][i] == True):
                    x= df['Cookie Options'][i]

                    if x == 'Decline All, Accept All, Customize cookies':         
                        alist.append(True)
                    else:
                        alist.append(False)

                else:
                    alist.append(False)
                    
            else:
                alist.append(True)

        df['Consent_compliant'] = alist                                           
        return df

    '''------------------------------------------------------------------------------------------'''
    
    # Helper function to extract data collected by each cookie
    def collect_data(data, i):                                                   
    
        for i in range(len(data)):
            words_list = (df['Data Collected '][i].split(';'))
        
        return words_list

    # Check if personal data is collected and user rights are informed in the policy
    def is_personal_data(dataframe, collected_data, cookie_policy_set):           
        for item in collected_data:                                               
            
            if any(item in personal_data for item in collected_data):

                if user_right_policy.issubset(cookie_policy_set):
                    return True
                
                return False
            
        return True
    
    '''-----------------------------------------------------------------------------------------'''
    
    # Check 3: Evaluating cookie policy compliance
    
    def is_policy_compliant(df):

        alist = []
        for i in range(len(df['Cookie Policy'])):
            cookie_policy_set = set(df['Cookie Policy'][i].split('\n'))
            cookie_purpose = {df['Purpose'][i]}
            collected_data = collect_data(df,i)

            # Checking essential cookies are cookie policy compliant (refer decision tree for the rules):
            if cookie_purpose.issubset(essential_purposes):

                if (df['SameParty (if cookie keeps data locally or sends it outside)'][i] == False) and (
                    policy_essential & third_party_policy).issubset(cookie_policy_set):

                    alist.append(is_personal_data(df['Origin'][i], collected_data, cookie_policy_set))

                elif (df['SameParty (if cookie keeps data locally or sends it outside)'][i] == True) and (
                    policy_essential).issubset(cookie_policy_set):

                    alist.append(is_personal_data(df['Origin'][i], collected_data, cookie_policy_set))

                else:
                    alist.append(False)

            # Checking non-essential cookies are cookie policy compliant (refer decision tree for the rules):
            elif cookie_purpose.issubset(non_essential_purposes):

                if (df['SameParty (if cookie keeps data locally or sends it outside)'][i] == False) and (
                    policy_non_essential & third_party_policy).issubset(cookie_policy_set):

                    alist.append(is_personal_data(df['Origin'][i], collected_data, cookie_policy_set))

                elif (df['SameParty (if cookie keeps data locally or sends it outside)'][i] == True) and (
                    policy_non_essential).issubset(cookie_policy_set):

                    alist.append(is_personal_data(df['Origin'][i], collected_data, cookie_policy_set))

                else:
                    alist.append(False)

        # Adding a field to indicate policy compliance
        df['Transparency compliant'] = alist                  
        return df
    
    '''-----------------------------------------------------------------------------------------'''
    
    # Function to identify reasons for policy non-compliance
    def policy_non_compliant_reasons(df): 

        # Key phrases for various compliance checks
        policy_basic = {'Types of CookiesHere are some examples of the types of cookies we use:'}
        policy_cookie_origin = {'Cookie Origin'}
        policy_third_party = {'Third-Party Processing'}
        policy_consent = {'Consent'}
        policy_managing_cookies = {'Managing Cookies'}
        user_right_policy = {'What Are Your Rights'}

        # Lists to store compliance status for each parameter
        policy_basic_list =[]
        policy_cookie_origin_list =[]
        policy_consent_list = []
        policy_manage_cookies_list = []
        policy_for_third_party_list = []
        policy_user_right_list = []
        
        # Starting iteration checking each policy parameter for compliance:
        for i in range(len(df['Cookie Policy'])):

            # Converting cookie policy content into a set of data
            cookie_policy_in_set = set(df['Cookie Policy'][i].split('\n'))  

            # Converting cookie purpose into a set for checking in other sets of data later
            cookie_purpose = {df['Purpose'][i]}   

            # Calling 'collect_data' function to get list of data collected by each cookie                          
            collected_data = collect_data(df, i)                            

            # Checking the cookie type is mentioned in the cookie policy:
            if (policy_basic).issubset(cookie_policy_in_set):
                policy_basic_list.append(True)
            else:
                policy_basic_list.append(False)

            # Checking the cookie origin is mentioned in the cookie policy:
            if (policy_cookie_origin).issubset(cookie_policy_in_set):
                policy_cookie_origin_list.append(True)
            else:
                policy_cookie_origin_list.append(False)

            # Checking consent is asked in the cookie policy:
            if (policy_consent).issubset(cookie_policy_in_set):
                policy_consent_list.append(True)
            else:
                policy_consent_list.append(False)

            # Checking managing cookies is mentioned in the cookie policy:
            if (policy_managing_cookies).issubset(cookie_policy_in_set):
                policy_manage_cookies_list.append(True)
            else:
                policy_manage_cookies_list.append(False)
            
            # Checking user's rights are informed in the cookie policy:
            if user_right_policy.issubset(cookie_policy_in_set):
                policy_user_right_list.append(True)
            else:
                policy_user_right_list.append(False)

            # Checking third party processing of data is mentioned in the cookie policy:
            if policy_third_party.issubset(cookie_policy_in_set):
                policy_for_third_party_list.append(True)
            else:
                policy_for_third_party_list.append(False)

        # Adding fields for compliance status to the dataframe    
        df['cookie type informed'] = policy_basic_list
        df['cookie origin informed'] = policy_cookie_origin_list
        df['consent asked'] = policy_consent_list
        df['manage cookies informed'] = policy_manage_cookies_list
        df['Third party policy informed'] = policy_for_third_party_list
        df['user right informed'] = policy_user_right_list

        return df                                    

    '''--------------------------------------------------------------------------------------'''
    
    # Conducting total compliance check
    def total_compliance_check(df):                     
        
        # Check retention compliance
        is_retention_compliant(df)               

        # Check consent compliance       
        is_banner_compliant(df)

        # Check transparency compliance                        
        is_policy_compliant(df)  
                      
        alist=[]
        for i in range(len(df)):

            if df['Retention compliant'][i]==True:
                if df['Consent_compliant'][i]==True:
                    if df['Transparency compliant'][i]==True:
                        alist.append(True)
                    else:
                        alist.append(False)
                else:
                    alist.append(False)
            else:
                alist.append(False)

        # Adding final compliance field
        df['Is compliant'] = alist                      
        
        # Adding non-compliance reasons fields
        policy_non_compliant_reasons(df)  

        df.reset_index(inplace=True)
        return df
    '''---------------------------------------------------------------------------------------------'''
    
    # Running all compliance checks
    total_compliance_check(df)                          

    # Summarizing compliance results
    compliance_summary = {
        'Overall compliance Rate (%)': (((df['Is compliant']==True).sum())/(df['Is compliant'].count())) * 100,
        'Retention compliance rate (%)': ((df['Retention compliant']==True).sum()/(df['Is compliant'].count()))*100,
        'Consent compliance rate (%)': ((df['Consent_compliant']==True).sum()/(df['Is compliant'].count()))*100,
        'Transparency compliance rate (%)': ((df['Transparency compliant']==True).sum()/(df['Is compliant'].count()))*100,

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

    # Saving the analyzed data to an excel file
    df.to_excel(output_filename, index=False)
    print(f"Analyzed data saved to {output_filename}")

    return df, compliance_summary

# Running the compliance analysis
new_df, summary,  = analyze_cookie_compliance(df, "output/cookie_compliance_analysis.xlsx")

# 3: Displaying the compliance summary
print("\nCompliance Summary:\n")
for key, value in summary.items():
    print(f"{key}: {value}")