import { NextRequest, NextResponse } from 'next/server'
import jwt from 'jsonwebtoken'

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production'

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()

    // Validate input
    if (!email || !password) {
      return NextResponse.json(
        { message: 'Email and password are required' },
        { status: 400 }
      )
    }

    // Demo authentication (in production, query database)
    if (email === 'demo@aether.com' && password === 'demo123') {
      const token = jwt.sign(
        { email, name: 'Demo User' },
        JWT_SECRET,
        { expiresIn: '7d' }
      )

      return NextResponse.json({
        token,
        user: { email, name: 'Demo User' },
      })
    }

    return NextResponse.json(
      { message: 'Invalid email or password' },
      { status: 401 }
    )
  } catch (error) {
    return NextResponse.json(
      { message: 'An error occurred' },
      { status: 500 }
    )
  }
}
