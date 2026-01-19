# Page snapshot

```yaml
- generic [ref=e2]:
  - region "Notifications alt+T"
  - generic [ref=e4]:
    - generic [ref=e5]:
      - heading "Configure Your Node" [level=1] [ref=e6]
      - paragraph [ref=e7]: Set up your identity on the .multiversemesh network
    - generic [ref=e8]:
      - generic [ref=e9]:
        - generic [ref=e10]: Mesh Name *
        - textbox "Mesh Name *" [active] [ref=e11]:
          - /placeholder: e.g., alice, food-coop, bridge-01
        - paragraph [ref=e12]:
          - text: "Your address:"
          - strong [ref=e13]: yourname.multiversemesh
      - generic [ref=e14]:
        - generic [ref=e15]: Description (optional)
        - textbox "Description (optional)" [ref=e16]:
          - /placeholder: e.g., Personal device, Community hub
      - generic [ref=e17]:
        - generic [ref=e18]: Contact Info (optional)
        - textbox "Contact Info (optional)" [ref=e19]:
          - /placeholder: e.g., alice@example.com, @alice
      - generic [ref=e20]:
        - paragraph [ref=e21]: Services
        - generic [ref=e22]:
          - checkbox "Share AI compute with the mesh" [ref=e23]
          - generic [ref=e24]:
            - strong [ref=e25]: Share AI compute
            - text: with the mesh
        - generic [ref=e26]:
          - checkbox "Act as bridge between mesh islands" [ref=e27]
          - generic [ref=e28]:
            - strong [ref=e29]: Act as bridge
            - text: between mesh islands
      - button "Configure Node" [disabled] [ref=e30]
    - paragraph [ref=e32]: This is a one-time setup. You can change these settings later.
```