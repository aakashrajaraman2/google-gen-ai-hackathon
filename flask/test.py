# Example: Create a list of file paths

from comparison import get_summary_jsons
docs = [
    r'german_docs\ADAC Malaysia Plus Membership.pdf',
    r'german_docs\ADAC Plus Mitgliedschaft.pdf',
    r'german_docs\ADAC Premium Mitgliedschaft.pdf',
   r'german_docs\BASIS MITGLIEDSCHAFT VON MOBIL IN DEUTSCHLAND E.V.pdf',
    r'german_docs\ERGO Schutzbrief.pdf',
    r'german_docs\KS Auxilia Schutzbrief.pdf'
]

# Call the function with the list of file paths
get_summary_jsons(docs)
