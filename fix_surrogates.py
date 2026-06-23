# Fix 1: replace surrogate pairs with proper Unicode in the bot file
with open('scenx_bot.py', encoding='utf-8', errors='surrogatepass') as f:
    c = f.read()

# Surrogate pairs → proper Unicode code points
# \ud83d\uddbc = U+1F5BC = 🖼
c = c.replace('\ud83d\uddbc', '\U0001f5bc')
# \ud83c\udfa8 = U+1F3A8 = 🎨  
c = c.replace('\ud83c\udfa8', '\U0001f3a8')

with open('scenx_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('surrogate fix done')
