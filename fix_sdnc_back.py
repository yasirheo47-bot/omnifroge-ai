with open('scenx_bot.py', encoding='utf-8') as f:
    c = f.read()

# Fix dur back button (points to mode page)
c = c.replace(
    'callback_data="SDNC_start")],\n    ])\n\ndef _kb_sdnc_orient',
    'callback_data="SDNC_show_mode")],\n    ])\n\ndef _kb_sdnc_orient'
)

# Fix orient back button (points to dur page)
c = c.replace(
    'callback_data="SDNC_start")],\n    ])\n\ndef _kb_sdnc_res',
    'callback_data="SDNC_BACK_DUR")],\n    ])\n\ndef _kb_sdnc_res'
)

with open('scenx_bot.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('done')
