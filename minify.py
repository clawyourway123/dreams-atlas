
import re

with open('/Users/clawdy/.openclaw/workspace/dreams-atlas/atlas-viewer-lab.js', 'r') as f:
    content = f.read()

# Remove comments
content = re.sub(r'//.*', '', content)
content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

# Remove extra whitespace
content = re.sub(r'\s+', ' ', content)
content = content.replace('{ ', '{').replace(' }', '}').replace('( ', '(').replace(' )', ')')

with open('/Users/clawdy/.openclaw/workspace/dreams-atlas/atlas-viewer-lab.min.js', 'w') as f:
    f.write(content.strip())
