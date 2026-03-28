'use client';

import { useState, FormEvent } from 'react';

type FormState = 'idle' | 'submitting' | 'success' | 'error';

export default function ContactForm() {
  const [state, setState] = useState<FormState>('idle');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [interest, setInterest] = useState('Partnership / Collaboration');
  const [message, setMessage] = useState('');

  function handleSubmit(e: FormEvent) {
    e.preventDefault();

    if (!name.trim() || !email.trim() || !message.trim()) {
      return;
    }

    setState('submitting');

    // Build mailto link as fallback (no backend)
    const subject = encodeURIComponent(
      `DREAMS Atlas Inquiry: ${interest}`,
    );
    const body = encodeURIComponent(
      `Name: ${name}\nEmail: ${email}\nInterest: ${interest}\n\n${message}`,
    );
    const mailto = `mailto:contact@kdense.science?subject=${subject}&body=${body}`;

    // Simulate brief processing then open mail client
    setTimeout(() => {
      window.location.href = mailto;
      setState('success');
    }, 400);
  }

  if (state === 'success') {
    return (
      <div className="rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
        <div className="text-center py-8">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-accent-100">
            <svg className="h-6 w-6 text-accent-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-semibold">Message Ready</h3>
          <p className="mt-2 text-sm text-gray-600">
            Your email client should have opened with your message pre-filled.
            If it didn&apos;t, you can reach us directly at{' '}
            <a href="mailto:contact@kdense.science" className="text-primary-600 underline">
              contact@kdense.science
            </a>
          </p>
          <button
            onClick={() => {
              setState('idle');
              setName('');
              setEmail('');
              setMessage('');
            }}
            className="mt-6 text-sm font-medium text-primary-600 hover:text-primary-700"
          >
            Send another message
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
      <h2 className="text-xl font-bold">Send a Message</h2>
      <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Name
          </label>
          <input
            type="text"
            id="name"
            name="name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            placeholder="Your name"
          />
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            type="email"
            id="email"
            name="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            placeholder="you@company.com"
          />
        </div>
        <div>
          <label htmlFor="interest" className="block text-sm font-medium text-gray-700">
            Interest
          </label>
          <select
            id="interest"
            name="interest"
            value={interest}
            onChange={(e) => setInterest(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            <option>Partnership / Collaboration</option>
            <option>Licensing</option>
            <option>Investment</option>
            <option>Technical Inquiry</option>
            <option>Other</option>
          </select>
        </div>
        <div>
          <label htmlFor="message" className="block text-sm font-medium text-gray-700">
            Message
          </label>
          <textarea
            id="message"
            name="message"
            rows={4}
            required
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            placeholder="Tell us about your project..."
          />
        </div>
        <button
          type="submit"
          disabled={state === 'submitting'}
          className="btn-primary w-full justify-center disabled:opacity-60"
        >
          {state === 'submitting' ? 'Opening email...' : 'Send Message'}
        </button>
      </form>
    </div>
  );
}
