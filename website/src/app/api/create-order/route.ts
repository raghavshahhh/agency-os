import { NextRequest, NextResponse } from 'next/server'

// Razorpay integration
const RAZORPAY_KEY_ID = process.env.RAZORPAY_KEY_ID || 'rzp_test_xxx'
const RAZORPAY_KEY_SECRET = process.env.RAZORPAY_KEY_SECRET || 'secret_xxx'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { amount, currency, receipt, notes } = body

    // Create Razorpay order
    const auth = Buffer.from(`${RAZORPAY_KEY_ID}:${RAZORPAY_KEY_SECRET}`).toString('base64')

    const response = await fetch('https://api.razorpay.com/v1/orders', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Basic ${auth}`,
      },
      body: JSON.stringify({
        amount,
        currency,
        receipt,
        notes,
        payment_capture: 1,
      }),
    })

    if (!response.ok) {
      const error = await response.text()
      console.error('Razorpay error:', error)
      return NextResponse.json({ error: 'Failed to create order' }, { status: 500 })
    }

    const order = await response.json()

    // Send confirmation email (Resend)
    await sendConfirmationEmail(notes.customer_email, notes.customer_name, order.id, amount)

    // Save to CRM
    await saveToCRM({
      name: notes.customer_name,
      email: notes.customer_email,
      phone: notes.customer_phone,
      company: notes.company,
      plan: notes.plan,
      amount: amount / 100,
      order_id: order.id,
      status: 'payment_pending',
      created_at: new Date().toISOString(),
    })

    return NextResponse.json({
      orderId: order.id,
      amount: order.amount,
      currency: order.currency,
    })

  } catch (error) {
    console.error('Error:', error)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}

async function sendConfirmationEmail(email: string, name: string, orderId: string, amount: number) {
  try {
    const RESEND_API_KEY = process.env.RESEND_API_KEY || 're_xxx'

    await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: 'Raghav@ragspro.com',
        to: [email],
        subject: 'Payment Link - RAGS Pro',
        text: `Hi ${name},

Thank you for booking with RAGS Pro!

Order ID: ${orderId}
Amount: ₹${(amount / 100).toLocaleString()}

Please complete the payment to start your project:
[Payment Link will be added here]

After payment, I'll reach out within 24 hours to discuss requirements.

Best,
Raghav
RAGS Pro`,
      }),
    })
  } catch (e) {
    console.error('Email error:', e)
  }
}

async function saveToCRM(data: any) {
  // Save to local JSON for now
  const fs = require('fs')
  const path = require('path')

  const crmPath = path.join(process.cwd(), '..', '..', 'data', 'crm_clients.json')

  let clients = []
  if (fs.existsSync(crmPath)) {
    clients = JSON.parse(fs.readFileSync(crmPath, 'utf-8'))
  }

  clients.push(data)
  fs.writeFileSync(crmPath, JSON.stringify(clients, null, 2))
}
