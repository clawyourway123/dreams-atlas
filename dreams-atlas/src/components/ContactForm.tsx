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
      <div className="rounded-panel border border-white/5 bg-surface/60 p-8 shadow-card">
        <div className="text-center py-8">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-teal-400/10">
            <svg className="h-6 w-6 text-teal-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-semibold text-white">Message Ready</h3>
          <p className="mt-2 text-sm text-navy-300">
            Your email client should have opened with your message pre-filled.
            If it didn&apos;t, you can reach us directly at{' '}
            <a href="mailto:contact@kdense.science" className="text-teal-400 underline">
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
            className="mt-6 text-sm font-medium text-teal-400 hover:text-teal-300"
          >
            Send another message
          </button>
        </div>
      </div>
    );
  }

  const inputClasses =
    'mt-1 block w-full rounded-card border border-white/10 bg-navy-900 px-4 py-2.5 text-sm text-white shadow-sm placeholder:text-navy-500 focus:border-teal-400 focus:outline-none focus:ring-1 focus:ring-teal-400';

  return (
    <div className="rounded-panel border border-white/5 bg-surface/60 p-8 shadow-card">
      <h2 className="text-xl font-bold text-white">Send a Message</h2>
      <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-navy-200">
            Name
          </label>
          <input
            type="text"
            id="name"
            name="name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={inputClasses}
            placeholder="Your name"
          />
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-navy-200">
            Email
          </label>
          <input
            type="email"
            id="email"
            name="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClasses}
            placeholder="you@company.com"
          />
        </div>
        <div>
          <label htmlFor="interest" className="block text-sm font-medium text-navy-200">
            Interest
          </label>
          <select
            id="interest"
            name="interest"
            value={interest}
            onChange={(e) => setInterest(e.target.value)}
            className={inputClasses}
          >
            <option>Partnership / Collaboration</option>
            <option>Licensing</option>
            <option>Investment</option>
            <option>Technical Inquiry</option>
            <option>Other</option>
          </select>
        </div>
        <div>
          <label htmlFor="message" className="block text-sm font-medium text-navy-200">
            Message
          </label>
          <textarea
            id="message"
            name="message"
            rows={4}
            required
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className={inputClasses}
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
