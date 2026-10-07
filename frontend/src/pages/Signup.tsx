import { useState, type ChangeEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi, type SignupData } from '../api'
import { useAuth } from '../auth'

const EMPTY: SignupData = { first_name: '', last_name: '', email: '', password: '', confirm_password: '' }

export default function Signup() {
  const { setUser } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<SignupData>(EMPTY)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const field = (key: keyof SignupData) => ({
    value: form[key],
    onChange: (e: ChangeEvent<HTMLInputElement>) => setForm({ ...form, [key]: e.target.value }),
    required: true,
  })
  const mismatch = form.confirm_password !== '' && form.password !== form.confirm_password

  return (
    <div className="page form-page">
      <h1>Create Account</h1>
      <form
        className="form"
        onSubmit={async (e) => {
          e.preventDefault()
          if (mismatch) return
          setError('')
          setBusy(true)
          try {
            setUser(await authApi.signup(form))
            navigate('/')
          } catch (err) {
            setError((err as Error).message)
          } finally {
            setBusy(false)
          }
        }}
      >
        <label>
          First name
          <input {...field('first_name')} autoComplete="given-name" />
        </label>
        <label>
          Last name
          <input {...field('last_name')} autoComplete="family-name" />
        </label>
        <label>
          Email
          <input type="email" {...field('email')} autoComplete="email" />
        </label>
        <label>
          Password
          <input type="password" {...field('password')} minLength={8} autoComplete="new-password" />
        </label>
        <label>
          Confirm password
          <input type="password" {...field('confirm_password')} autoComplete="new-password" />
        </label>
        {mismatch && <p className="error">Passwords do not match.</p>}
        {error && <p className="error">{error}</p>}
        <button className="btn" type="submit" disabled={busy || mismatch}>
          {busy ? 'Creating account…' : 'Create Account'}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  )
}
