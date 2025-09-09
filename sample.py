missMatch_carList = ['Y','M','n','C' ,'5', '1', '9', '4', '9', '8']  # Example list
number_mapping_rotate = {
    0: 'ZERO', 
    1: 'ONE', 
    2: 'TWO', 
    3: 'THREE', 
    4: 'FOUR', 
    5: 'FIVE', 
    6: 'SIX', 
    7: 'SEVEN', 
    8: 'EIGHT', 
    9: 'NINE', 
    10: 'TEN'
} 
# Mapping numeric values in missMatch_carList to their corresponding words
mapped_list_new = [
    number_mapping_rotate[int(item)] if item.isdigit() and int(item) in number_mapping_rotate else item
    for item in missMatch_carList
]

# Print the mapped list
print("Mapped list is:", mapped_list_new)
