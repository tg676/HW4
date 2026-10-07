import { Fragment, useEffect } from 'react'
import { NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from './auth'
import ChatWidget from './components/ChatWidget'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import About from './pages/About'
import Login from './pages/Login'
import Signup from './pages/Signup'

const links = [
  { to: '/', label: 'Home' },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function App() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()

  // New page → start at the top (product pages especially).
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <>
      <div className="marquee" aria-hidden="true">
        <div className="marquee-track">
          {[0, 1].map((k) => (
            <Fragment key={k}>
              <span>Boola Boola</span>
              <span>Officially licensed Yale apparel</span>
              <span>Visit us at 57 Broadway, New Haven</span>
              <span>Ask the Bulldog for live sizes &amp; stock</span>
              <span>Residential colleges · Varsity sports · Family gear</span>
            </Fragment>
          ))}
        </div>
      </div>
      <header className="navbar">
        <NavLink to="/" className="brand">
          <span className="brand-mark">Y</span>
          <span>
            Campus Customs
            <small>NEW HAVEN · EST. ON BROADWAY</small>
          </span>
        </NavLink>
        <nav>
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.to === '/'}>
              {l.label}
            </NavLink>
          ))}
          {user ? (
            <>
              <span className="nav-user">Hi, {user.first_name}</span>
              <button
                className="nav-btn"
                onClick={async () => {
                  await logout()
                  navigate('/')
                }}
              >
                Log Out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">Login</NavLink>
              <NavLink to="/signup">Create Account</NavLink>
            </>
          )}
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:id" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="*" element={<p className="page">Page not found.</p>} />
        </Routes>
      </main>

      <footer className="footer">
        <strong>Campus Customs</strong>
        57 Broadway, New Haven, CT · Officially licensed Yale merchandise · For God, for Country, and for Yale
      </footer>

      <ChatWidget />
    </>
  )
}
