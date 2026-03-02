import re

with open("csao_dashboard_improved.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update tailwind config
tailwind_config_old = """          colors: {
            "zomato": "#E23744",
            "zomato-dark": "#CB202D",
            "background-light": "#FAFAFA",
            "background-dark": "#0F0F0F",
            "card-dark": "#1A1A1A",
            "border-subtle": "#2A2A2A",
          },"""

tailwind_config_new = """          colors: {
            "primary": "#F5B800",
            "primary-dark": "#E5A800",
            "secondary": "#5BA8B0",
            "background-light": "#D4E5E8",
            "background-dark": "#0F0F0F",
            "card-dark": "#1A1A1A",
            "border-subtle": "rgba(255, 255, 255, 0.08)",
          },"""
html = html.replace(tailwind_config_old, tailwind_config_new)

# Update Zomato classes to primary
html = html.replace("bg-zomato", "bg-primary")
html = html.replace("text-zomato", "text-primary")
html = html.replace("border-zomato", "border-primary")

# 2. Add New CSS
css_old_start = "/* Smooth transitions */"
css_new = """/* Smooth transitions */
    * {
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Professional focus states */
    button:focus, select:focus, input:focus {
      outline: none;
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05), 0 0 0 3px rgba(245, 184, 0, 0.3);
    }
    
    /* Glassmorphism Classes */
    .glass-card {
      background: rgba(26, 26, 26, 0.6);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-radius: 24px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04);
    }

    .glass-card-sm {
      background: rgba(26, 26, 26, 0.5);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-radius: 16px;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .glass-sidebar {
      background: rgba(26, 26, 26, 0.65);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Hover states for Recommendation Cards */
    .card-hover {
      transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.4s ease, border-color 0.4s ease;
    }
    
    .card-hover:hover {
      transform: scale(1.03) translateY(-4px);
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2), 0 0 24px rgba(245, 184, 0, 0.12);
      border-color: rgba(245, 184, 0, 0.3);
    }

    /* Primary Button Glow */
    .btn-primary {
      background: linear-gradient(135deg, #F5B800 0%, #E5A800 100%);
      color: #1A1A1A;
      box-shadow: 0 4px 12px rgba(245, 184, 0, 0.4);
      border-radius: 24px;
      font-weight: 700;
    }
    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(245, 184, 0, 0.5);
    }

    /* Gradient overlay for cards */
    .card-gradient-overlay {
      position: absolute;
      inset: 0;
      background: linear-gradient(to bottom, transparent 40%, rgba(0,0,0,0.6) 100%);
      pointer-events: none;
      z-index: 1;
    }

    /* Text hierarchy */
    .tracking-tight-heading {
      letter-spacing: -0.5px;
    }
    
    /* Decorative Textures */
    .texture-overlay {
      position: absolute;
      inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.04'/%3E%3C/svg%3E");
      pointer-events: none;
      z-index: 0;
    }"""
html = html.replace("""/* Smooth transitions */
    * {
      transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
    }""", css_new)

# Remove old focus states
html = re.sub(r'/\* Professional focus states \*/.*?/\* Confidence bar animation \*/', '/* Confidence bar animation */', html, flags=re.DOTALL)
html = re.sub(r'/\* Hover states \*/.*?/\* Professional badge styles \*/', '/* Professional badge styles */', html, flags=re.DOTALL)
html = re.sub(r'/\* Remove excessive shadows \*/.*?</style>', '</style>', html, flags=re.DOTALL)

# 3. Add background decorative elements
body_start = '<body class="bg-background-dark text-slate-100 antialiased">'
body_new = """<body class="bg-background-dark text-slate-100 antialiased relative">
<!-- Decorative Background Elements -->
<div class="fixed top-[-15%] left-[-10%] w-[600px] h-[600px] rounded-full bg-primary/10 blur-[120px] pointer-events-none z-0"></div>
<div class="fixed bottom-[-10%] right-[-5%] w-[800px] h-[800px] rounded-full bg-secondary/10 blur-[120px] pointer-events-none z-0"></div>
<div class="fixed inset-0 texture-overlay z-0"></div>"""
html = html.replace(body_start, body_new)

# 4. Modify classes for layout
html = html.replace('class="flex h-screen overflow-hidden"', 'class="flex h-screen overflow-hidden relative z-10"')

# Sidebar
html = html.replace('class="w-[360px] border-r border-border-subtle flex flex-col bg-card-dark overflow-y-auto scrollbar-hide"', 
                    'class="w-[360px] flex flex-col glass-sidebar overflow-y-auto scrollbar-hide"')

# Top Metrics Cards
html = html.replace('bg-card-dark p-5 rounded-lg border border-border-subtle subtle-shadow', 
                    'glass-card p-6 relative overflow-hidden group')

html = html.replace('rounded-lg bg-primary/10', 'rounded-xl bg-primary/15')
html = html.replace('bg-blue-500/10', 'bg-secondary/20')
html = html.replace('text-blue-400', 'text-secondary')
html = html.replace('bg-green-500/10', 'bg-green-500/15')
html = html.replace('bg-purple-500/10', 'bg-purple-500/15')

# Recommendation Cards
html = html.replace('bg-card-dark rounded-lg border border-border-subtle subtle-shadow card-hover overflow-hidden',
                    'glass-card card-hover overflow-hidden relative group')
html = html.replace('<div class="p-4">', '<div class="card-gradient-overlay rounded-b-[24px]"></div><div class="p-5 relative z-10 h-full flex flex-col">')

# Recommendation buttons
html = html.replace('w-full py-2.5 rounded-lg bg-primary/10 text-primary text-xs font-semibold hover:bg-primary hover:text-white transition-all',
                    'mt-auto w-full py-3 rounded-xl bg-primary/10 text-primary text-sm font-semibold hover:bg-primary hover:text-[#1A1A1A] transition-all')

# Change headings
html = html.replace('text-xl font-bold mb-1', 'text-2xl font-bold mb-1 tracking-tight-heading')
html = html.replace('text-base font-bold tracking-tight', 'text-lg font-bold tracking-tight-heading')
html = html.replace('text-2xl font-bold', 'text-3xl font-bold tracking-tight-heading')

# Insights
html = html.replace('bg-card-dark rounded-lg border border-border-subtle p-6', 'glass-card p-8')

# Primary Update CTA
html = html.replace('w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3 rounded-lg transition-all flex items-center justify-center gap-2',
                    'btn-primary w-full py-4 transition-all flex items-center justify-center gap-2 text-[15px]')

# Menu items
html = html.replace('p-3 rounded-lg bg-background-dark border border-border-subtle hover:border-slate-600 transition-colors group',
                    'p-3.5 glass-card-sm hover:border-secondary/40 transition-colors group')

# Add "hover-scale" to thumbnail cards
html = html.replace('w-7 h-7 rounded-lg bg-primary/10', 'w-8 h-8 rounded-lg bg-primary/15 hover:scale-105')

# Text shadow for better contrast against glass
html = html.replace('text-lg font-bold text-white mb-4', 'text-xl font-bold text-white mb-4 drop-shadow-md')

# User segment buttons
html = html.replace('p-3 rounded-lg bg-background-dark border border-border-subtle', 'p-3 glass-card-sm border-white/5')
html = html.replace('p-3 rounded-lg bg-primary/10 border-2 border-primary', 'p-3 glass-card-sm border-2 border-primary bg-primary/5')

with open("csao_dashboard_improved.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Redesign applied successfully.")
