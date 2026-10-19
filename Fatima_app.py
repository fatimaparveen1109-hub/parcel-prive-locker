import streamlit as st
from sqlalchemy import text
import Fatima_database as db, Fatima_auth as auth, Fatima_services as sv
from Fatima_database import get_engine, rows, one, DEMO, users, hubs, lockers, products

st.set_page_config(page_title="Parcel Privé", page_icon="📦", layout="wide", initial_sidebar_state="collapsed")
db.init_db(); auth.bootstrap()
st.markdown("""<style>
.stApp{background:#F6F8FA}.block-container{padding-top:1rem;max-width:1100px}
.nav{background:#0B1F3A;color:#fff;padding:.7rem 1rem;border-radius:12px;display:flex;justify-content:space-between;margin-bottom:1rem}
.nav b{color:#2DD4BF}.hero{background:linear-gradient(135deg,#0B1F3A,#0F766E);color:#fff;padding:2.2rem 1.5rem;border-radius:16px}
.hero h1{color:#fff;font-size:clamp(1.6rem,5vw,2.6rem)}.card{background:#fff;border:1px solid #E5E9EF;border-radius:12px;padding:1rem;margin:.4rem 0}
.badge{background:#CCFBF1;color:#0F766E;border-radius:99px;padding:2px 10px;font-size:.8rem;font-weight:600}
.stButton>button{background:#0F766E;color:#fff;border:0;border-radius:8px}.foot{color:#667;text-align:center;padding:2rem 0;font-size:.85rem}
</style>""", unsafe_allow_html=True)
S = st.session_state
U = S.get("user")
hubmap = lambda: {h["id"]: h["name"] for h in rows(get_engine().connect(), "SELECT id,name FROM hubs WHERE active=:a", a=True)}
badge = lambda s: f"<span class='badge'>{s}</span>"

st.markdown(f"<div class='nav'><span>📦 <b>Parcel Privé</b></span><span>{U['name']+' · '+U['role'] if U else 'Privacy-first parcel delivery'}</span></div>", unsafe_allow_html=True)
if DEMO:
    st.warning("DEMO MODE: no database configured. Data is temporary and may be lost on restart. Demo logins use password demo12345 (admin@/seller@/rider@/customer@demo.test).")

def landing():
    st.markdown("<div class='hero'><h1>Your Parcel. Your Privacy. Smarter Delivery.</h1><p>Parcel Privé delivers online orders to secure automated locker hubs, so sellers and riders never see your home address or phone number.</p></div>", unsafe_allow_html=True)
    st.subheader("How it works")
    st.write("🛒 Shop → 🏪 Seller prepares → 🛵 Rider delivers to hub → 🔔 You get notified → 🔐 You collect with QR")
    cols = st.columns(5)
    for col, (t, d) in zip(cols, [("Privacy Protection", "Address stays private"), ("Secure Locker Hubs", "Automated lockers"), ("QR-Based Access", "Expiring single-use tokens"),
                                  ("Parcel Tracking", "Live status timeline"), ("Backup Hub", "Only with your consent")]):
        col.markdown(f"<div class='card'><b>{t}</b><br><small>{d}</small></div>", unsafe_allow_html=True)
    a, b = st.tabs(["Sign in", "Get started"])
    with a:
        e = st.text_input("Email", key="se"); p = st.text_input("Password", type="password", key="sp")
        if st.button("Sign in"):
            u = auth.signin(e, p)
            if u: S.user = u; S.cart = {}; st.rerun()
            else: st.error("Wrong email or password, or account disabled.")
    with b:
        role = st.selectbox("I am a", ["customer", "seller", "rider"])
        n = st.text_input("Full name"); e2 = st.text_input("Email", key="ge"); p2 = st.text_input("Password (8+ chars)", type="password", key="gp")
        ad = ph = loc = ""
        if role == "customer": ad = st.text_area("Home address (private)"); ph = st.text_input("Phone (private)")
        if role == "seller": loc = st.text_input("Pickup location for riders")
        if st.button("Create account"):
            err = auth.signup(e2, n, p2, role, ad, ph, loc)
            st.error(err) if err else st.success("Account created. Please sign in.")
    st.markdown("<div class='foot'>© Parcel Privé — Privacy-Based Automated Parcel Locker Delivery System · University project</div>", unsafe_allow_html=True)

def notes(uid):
    with get_engine().connect() as c:
        for n in rows(c, "SELECT message,at FROM notifications WHERE user_id=:u ORDER BY id DESC LIMIT 15", u=uid):
            st.caption(f"{n['at']:%d %b %H:%M} — {n['message']}")
        if not rows(c, "SELECT 1 x FROM notifications WHERE user_id=:u LIMIT 1", u=uid): st.info("No notifications yet.")

def customer():
    uid = U["id"]; t = st.tabs(["Shop", "Cart", "My orders", "Profile", "Notifications", "Support"])
    hm = hubmap()
    with t[0]:
        q = st.text_input("Search"); 
        with get_engine().connect() as c:
            cats = [r["category"] for r in rows(c, "SELECT DISTINCT category FROM products WHERE active=:a", a=True)]
            cat = st.selectbox("Category", ["All"] + cats)
            ps = rows(c, "SELECT p.id,p.name,p.category,p.price,p.description,p.stock,u.name seller FROM products p JOIN users u ON u.id=p.seller_id WHERE p.active=:a AND p.stock>0 AND LOWER(p.name) LIKE :q", a=True, q=f"%{q.lower()}%")
        ps = [p for p in ps if cat == "All" or p["category"] == cat]
        if not ps: st.info("No products found.")
        for p in ps:
            st.markdown(f"<div class='card'>📦 <b>{p['name']}</b> · ${float(p['price']):.2f}<br><small>{p['description']} · Seller: {p['seller']} · {p['stock']} left</small></div>", unsafe_allow_html=True)
            n = st.number_input("Qty", 1, int(p["stock"]), 1, key=f"q{p['id']}")
            if st.button("Add to cart", key=f"a{p['id']}"): S.cart[p["id"]] = n; st.toast("Added")
    with t[1]:
        if not S.cart: st.info("Your cart is empty.")
        else:
            for pid, q in list(S.cart.items()):
                with get_engine().connect() as c: p = one(c, "SELECT name,price FROM products WHERE id=:i", i=pid)
                st.write(f"{p['name']} × {q} — ${float(p['price'])*q:.2f}")
            if len(hm) < 2: st.error("At least two active hubs are needed.")
            else:
                pref = st.selectbox("Preferred hub", list(hm), format_func=hm.get)
                bk = st.selectbox("Backup hub (required)", [h for h in hm if h != pref], format_func=hm.get)
                cons = st.checkbox("I consent to my parcel being redirected to the backup hub ONLY if the preferred hub has no available locker.")
                if st.button("Place order"):
                    err, ids = sv.place_order(uid, S.cart, pref, bk, cons)
                    if err: st.error(err)
                    else: S.cart = {}; st.success("Order placed. Delivery ID(s): " + ", ".join(ids) + ". Payment is unverified until confirmed.")
    with t[2]:
        with get_engine().connect() as c:
            os_ = rows(c, "SELECT o.*,h.name hub FROM orders o LEFT JOIN hubs h ON h.id=COALESCE(o.actual_hub,o.pref_hub) WHERE customer_id=:u ORDER BY o.id DESC", u=uid)
        if not os_: st.info("No orders yet.")
        for o in os_:
            with st.expander(f"{o['delivery_id']} — {o['status']}"):
                st.markdown(f"Hub: **{o['hub']}** · Payment: {badge(o['payment_status'])}", unsafe_allow_html=True)
                with get_engine().connect() as c: hs = rows(c, "SELECT status,at FROM order_status_history WHERE order_id=:i ORDER BY id", i=o["id"])
                for h in hs: st.caption(f"✔ {h['status']} — {h['at']:%d %b %H:%M}")
                if o["pickup_deadline"]: st.write(f"Pickup deadline: {o['pickup_deadline']:%d %b %H:%M}")
                if o["status"] == "Awaiting Customer Hub":
                    nh = st.selectbox("Choose another hub", list(hm), format_func=hm.get, key=f"nh{o['id']}")
                    if st.button("Confirm new hub", key=f"cn{o['id']}"):
                        err = sv.customer_choose_hub(uid, o["id"], nh); st.error(err) if err else st.rerun()
                if o["status"] == "Ready for Pickup":
                    for purpose, label in (("room", "Room access QR"), ("pickup", "Locker pickup QR")):
                        if st.button(f"Generate {label}", key=f"{purpose}{o['id']}"):
                            raw, err = sv.issue_token(uid, o["id"], purpose)
                            if err: st.error(err)
                            else: st.image(sv.qr_image(raw), width=220); st.caption("Expires in 10 minutes. Single use.")
    with t[3]:
        with get_engine().connect() as c: pr = one(c, "SELECT address,phone FROM customer_private_details WHERE user_id=:u", u=uid)
        st.write(f"**{U['name']}** · {U['email']}"); st.caption("Private details (only you can see these):"); st.write(pr["address"], pr["phone"])
    with t[4]: notes(uid)
    with t[5]: st.write("Contact support through the admin team. Sellers and riders never receive your personal details.")

def seller():
    uid = U["id"]; t = st.tabs(["Orders", "Products", "Notifications"])
    with t[0]:
        with get_engine().connect() as c:  # NO customer columns are selected
            os_ = rows(c, "SELECT id,delivery_id,status,created_at FROM orders WHERE seller_id=:u ORDER BY id DESC", u=uid)
        if not os_: st.info("No orders yet.")
        for o in os_:
            with get_engine().connect() as c: its = rows(c, "SELECT p.name,i.qty FROM order_items i JOIN products p ON p.id=i.product_id WHERE i.order_id=:i", i=o["id"])
            items_txt = ', '.join(str(i['name']) + ' x ' + str(i['qty']) for i in its)
            st.markdown(f"<div class='card'><b>{o['delivery_id']}</b> {badge(o['status'])}<br>{items_txt}</div>", unsafe_allow_html=True)
            nxt = {"Order Placed": ["Seller Accepted", "Cancelled"], "Seller Accepted": ["Preparing"], "Preparing": ["Ready for Rider"]}.get(o["status"], [])
            cols = st.columns(max(len(nxt), 1))
            for col, n in zip(cols, nxt):
                if col.button("Reject" if n == "Cancelled" else n, key=f"{o['id']}{n}"):
                    err = sv.staff_action("seller", uid, o["id"], n); st.error(err) if err else st.rerun()
    with t[1]:
        with st.form("np"):
            n = st.text_input("Name"); cat = st.text_input("Category"); d = st.text_area("Description")
            pr = st.number_input("Price", 0.01, 100000.0, 10.0); stk = st.number_input("Stock", 0, 100000, 10); sz = st.selectbox("Parcel size", list("SML"))
            if st.form_submit_button("Add product") and n.strip():
                with get_engine().begin() as c: c.execute(products.insert().values(seller_id=uid, name=n, category=cat, description=d, price=pr, stock=stk, size=sz, active=True))
                st.rerun()
        with get_engine().connect() as c: ps = rows(c, "SELECT id,name,price,stock,active FROM products WHERE seller_id=:u", u=uid)
        for p in ps:
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2]); c1.write(p["name"])
            np_ = c2.number_input("Price", 0.01, 100000.0, float(p["price"]), key=f"pp{p['id']}"); ns = c3.number_input("Stock", 0, 100000, p["stock"], key=f"ps{p['id']}")
            act = c4.checkbox("Active", p["active"], key=f"pa{p['id']}")
            if st.button("Save", key=f"sv{p['id']}"):
                with get_engine().begin() as c: c.execute(text("UPDATE products SET price=:a,stock=:b,active=:c WHERE id=:i AND seller_id=:u"), {"a": np_, "b": ns, "c": act, "i": p["id"], "u": uid})
                st.rerun()
    with t[2]: notes(uid)

def rider():
    uid = U["id"]; t = st.tabs(["Available", "My deliveries", "Notifications"])
    # Only delivery ID, seller pickup location and hub info are selected - no customer data, no product names.
    base = "SELECT o.id,o.delivery_id,o.status,s.location pickup,h.name hub,h.area area FROM orders o JOIN users s ON s.id=o.seller_id LEFT JOIN hubs h ON h.id=COALESCE(o.actual_hub,o.pref_hub) "
    with t[0]:
        with get_engine().connect() as c: av = rows(c, base + "WHERE o.status='Ready for Rider' AND o.rider_id IS NULL")
        if not av: st.info("No parcels waiting for a rider.")
        for o in av:
            st.markdown(f"<div class='card'><b>{o['delivery_id']}</b><br>Pickup: {o['pickup']}<br>Hub: {o['hub']} ({o['area']})</div>", unsafe_allow_html=True)
            if st.button("Accept delivery", key=f"c{o['id']}"):
                err = sv.rider_action(uid, o["id"], "claim"); st.error(err) if err else st.rerun()
    with t[1]:
        with get_engine().connect() as c: my = rows(c, base + "WHERE o.rider_id=:u ORDER BY o.id DESC", u=uid)
        if not my: st.info("No deliveries yet.")
        for o in my:
            st.markdown(f"<div class='card'><b>{o['delivery_id']}</b> {badge(o['status'])}<br>Pickup: {o['pickup']}<br>Hub: {o['hub']} ({o['area']})</div>", unsafe_allow_html=True)
            act = {"Rider Assigned": ("pickup", "Confirm pickup from seller"), "In Transit": ("arrive", "Confirm arrival near hub"), "Locker Reserved": ("deposit", "Report parcel deposited")}.get(o["status"])
            if o["status"] == "Locker Reserved":
                with get_engine().connect() as c: lk = one(c, "SELECT l.code FROM lockers l JOIN orders o ON o.locker_id=l.id WHERE o.id=:i", i=o["id"])
                st.info(f"Locker assigned: {lk['code']} (time-limited reservation)")
            if o["status"] == "Awaiting Customer Hub": st.warning("Both hubs full. Keep parcel secure; customer is choosing another hub.")
            if o["status"] == "Deposit Pending Verification": st.info("Waiting for admin verification of deposit.")
            if act and st.button(act[1], key=f"{act[0]}{o['id']}"):
                err = sv.rider_action(uid, o["id"], act[0]); st.error(err) if err else st.rerun()
    with t[2]: notes(uid)

def admin():
    uid = U["id"]
    with get_engine().begin() as c: sv.expire_reservations(c)
    t = st.tabs(["Overview", "Users", "Orders", "Hubs & Lockers", "QR & Security", "Payments", "Reports", "Logs"])
    with t[0], get_engine().connect() as c:
        k = one(c, "SELECT COUNT(*) a,SUM(CASE WHEN status='Order Placed' THEN 1 ELSE 0 END) p,SUM(CASE WHEN status='Ready for Pickup' THEN 1 ELSE 0 END) r,SUM(CASE WHEN status IN ('Rider Assigned','In Transit','Arrival Confirmed','Locker Reserved') THEN 1 ELSE 0 END) d FROM orders")
        av = one(c, "SELECT COUNT(*) n FROM lockers WHERE status='available'")["n"]
        a, b, cc, d, e = st.columns(5); a.metric("Orders", k["a"]); b.metric("Pending", k["p"] or 0); cc.metric("Active deliveries", k["d"] or 0); d.metric("Ready for pickup", k["r"] or 0); e.metric("Free lockers", av)
        st.dataframe(rows(c, "SELECT h.name,COUNT(l.id) total,SUM(CASE WHEN l.status='available' THEN 1 ELSE 0 END) free FROM hubs h LEFT JOIN lockers l ON l.hub_id=h.id GROUP BY h.name"), use_container_width=True)
    with t[1], get_engine().connect() as c:
        for u in rows(c, "SELECT id,name,email,role,active FROM users ORDER BY id"):  # no private details exposed
            c1, c2 = st.columns([4, 1]); c1.write(f"{u['name']} · {u['email']} · {u['role']} · {'active' if u['active'] else 'disabled'}")
            if u["id"] != uid and c2.button("Toggle", key=f"u{u['id']}"):
                with get_engine().begin() as c2_: c2_.execute(text("UPDATE users SET active=:a WHERE id=:i"), {"a": not u["active"], "i": u["id"]}); sv.log(c2_, f"admin:{uid}", "toggle_user", str(u["id"]))
                st.rerun()
    with t[2], get_engine().connect() as c:
        for o in rows(c, "SELECT id,delivery_id,status,payment_status FROM orders ORDER BY id DESC LIMIT 50"):
            st.markdown(f"<div class='card'><b>{o['delivery_id']}</b> {badge(o['status'])} pay: {o['payment_status']}</div>", unsafe_allow_html=True)
            if o["status"] == "Deposit Pending Verification" and st.button("Manually verify deposit", key=f"v{o['id']}"):
                err = sv.admin_verify_deposit(uid, o["id"]); st.error(err) if err else st.rerun()
            if o["status"] == "Ready for Pickup" and st.button("Manual collection", key=f"mc{o['id']}"):
                err = sv.admin_manual_collect(uid, o["id"]); st.error(err) if err else st.rerun()
            if o["status"] == "Expired" and st.button("Mark returned", key=f"rt{o['id']}"):
                err = sv.staff_action("admin", uid, o["id"], "Returned"); st.error(err) if err else st.rerun()
    with t[3]:
        with st.form("nh"):
            n = st.text_input("New hub name"); a = st.text_input("Area")
            if st.form_submit_button("Create hub") and n.strip():
                with get_engine().begin() as c: c.execute(hubs.insert().values(name=n, area=a, active=True)); sv.log(c, f"admin:{uid}", "create_hub", n)
                st.rerun()
        with get_engine().connect() as c: hs = rows(c, "SELECT id,name FROM hubs"); ls = rows(c, "SELECT l.id,l.code,l.size,l.status,h.name hub FROM lockers l JOIN hubs h ON h.id=l.hub_id")
        if hs:
            with st.form("nl"):
                hid = st.selectbox("Hub", [h["id"] for h in hs], format_func=lambda i: next(h["name"] for h in hs if h["id"] == i)); code = st.text_input("Locker code"); sz = st.selectbox("Size", list("SML"))
                if st.form_submit_button("Add locker") and code.strip():
                    with get_engine().begin() as c: c.execute(lockers.insert().values(hub_id=hid, code=code.strip(), size=sz, status="available")); sv.log(c, f"admin:{uid}", "add_locker", code)
                    st.rerun()
        for l in ls:
            c1, c2 = st.columns([4, 2]); c1.write(f"{l['hub']} · {l['code']} · {l['size']} · {l['status']}")
            if l["status"] in ("available", "maintenance") and c2.button("Toggle maintenance", key=f"m{l['id']}"):
                with get_engine().begin() as c: c.execute(text("UPDATE lockers SET status=:s WHERE id=:i"), {"s": "maintenance" if l["status"] == "available" else "available", "i": l["id"]}); sv.log(c, f"admin:{uid}", "locker_maint", l["code"])
                st.rerun()
    with t[4]:
        st.warning("Hardware/QR scanner not integrated. See Fatima_hardware.py and README for what to get from the other group.")
        with get_engine().connect() as c:
            st.dataframe(rows(c, "SELECT order_id,purpose,expires_at,used,revoked FROM qr_tokens ORDER BY id DESC LIMIT 30"), use_container_width=True)
            st.dataframe(rows(c, "SELECT * FROM hardware_events ORDER BY id DESC LIMIT 20"), use_container_width=True)
        raw = st.text_input("Test scanner input (paste token)"); pp = st.selectbox("Purpose", ["pickup", "room"])
        if st.button("Validate token") and raw: st.info(sv.verify_token(raw, pp))
    with t[5], get_engine().connect() as c:
        for o in rows(c, "SELECT id,delivery_id,payment_status FROM orders ORDER BY id DESC LIMIT 30"):
            c1, c2, c3 = st.columns([2, 3, 2]); c1.write(f"{o['delivery_id']} ({o['payment_status']})")
            ref = c2.text_input("Provider reference", key=f"r{o['id']}", label_visibility="collapsed", placeholder="transaction ref")
            if c3.button("Mark verified", key=f"pv{o['id']}") and ref.strip(): sv.admin_set_payment(uid, o["id"], ref, "verified"); st.rerun()
        st.caption("No payment provider is connected: 'verified' is a manual admin decision. Never enter card numbers.")
    with t[6], get_engine().connect() as c:
        st.dataframe(rows(c, "SELECT status,COUNT(*) orders FROM orders GROUP BY status"), use_container_width=True)
    with t[7], get_engine().connect() as c:
        st.dataframe(rows(c, "SELECT at,actor,action,detail FROM activity_logs ORDER BY id DESC LIMIT 100"), use_container_width=True)

if not U: landing()
else:
    with st.sidebar:
        st.write(f"Signed in: **{U['name']}**")
        if st.button("Log out"): S.clear(); st.rerun()
    # Role is taken from the server-verified session user, never from a frontend control.
    {"customer": customer, "seller": seller, "rider": rider, "admin": admin}[U["role"]]()
