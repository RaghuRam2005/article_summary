"use client"
import { Description, Field, Fieldset, Input, Label, Button } from '@headlessui/react'
import clsx from 'clsx'
import { Cover } from './components/cover';
import { BackgroundBeams } from './components/background';
import { Sign } from 'crypto';
import { useState } from 'react';

function SignUpPage({ onNavigate }: { onNavigate: (page: 'signup' | 'login') => void }) {
  const [displayName, setName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [userPass, setUserPass] = useState('')
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gray-900">
      <div className="w-full max-w-md px-4 relative z-10">
        <div>
          <h1 className="text-4xl md:text-4xl lg:text-6xl font-semibold max-w-7xl mx-auto text-center mt-6 relative z-20 py-6 bg-clip-text text-transparent bg-gradient-to-b from-neutral-800 via-neutral-700 to-neutral-700 dark:from-neutral-800 dark:via-white dark:to-white">
            SignUp to get <br /> <Cover>Started</Cover>
          </h1>
        </div>
        <Fieldset className="space-y-6 rounded-xl bg-white/5 p-6 sm:p-10">
          <Field>
            <Label className="text-sm/6 font-medium text-white">Name</Label>
            <Input required type='text' placeholder='Enter you name here' value={displayName} onChange={e => setName(e.target.value)}
              className={clsx(
                'mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white',
                'focus:not-data-focus:outline-none data-focus:outline-2 data-focus:-outline-offset-2 data-focus:outline-white/25'
              )}
            />
          </Field>
          <Field>
            <Label className="text-sm/6 font-medium text-white">Email</Label>
            <Input required type='email' placeholder='Enter you email here' value={userEmail} onChange={e => setUserEmail(e.target.value)}
              className={clsx(
                'mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white',
                'focus:not-data-focus:outline-none data-focus:outline-2 data-focus:-outline-offset-2 data-focus:outline-white/25'
              )}
            />
          </Field>
          <Field>
            <Label className="text-sm/6 font-medium text-white">Password</Label>
            <Input required type='password' placeholder='Enter your password here' value={userPass} onChange={e => setUserPass(e.target.value)}
              className={clsx(
                'mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white',
                'focus:not-data-focus:outline-none data-focus:outline-2 data-focus:-outline-offset-2 data-focus:outline-white/25'
              )}
            />
          </Field>
          <div className="flex justify-center">
            <Button onClick={handleSignup} className="inline-flex items-center gap-2 rounded-md bg-gray-700 px-3 py-1.5 text-sm/6 font-semibold text-white shadow-inner shadow-white/10 focus:not-data-focus:outline-none data-focus:outline data-focus:outline-white data-hover:bg-gray-600 data-open:bg-gray-700">
              Signup
            </Button>
          </div>
          <div className="text-center text-sm text-neutral-400 pt-4">
            Already have an account?{' '}
            <a href="" onClick={(e) => {
              e.preventDefault();
              onNavigate('login');
            }} className="font-semibold text-white hover:underline">
              Login instead
            </a>
          </div>
          
        </Fieldset>
      </div>
      <BackgroundBeams />
    </div>
  )
}

function LoginPage({ onNavigate }:{ onNavigate: (page: 'signup' | 'login') => void }) {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gray-900">
      <div className="w-full max-w-md px-4 relative z-10">
        <div>
          <h1 className="text-4xl md:text-4xl lg:text-6xl font-semibold max-w-7xl mx-auto text-center mt-6 relative z-20 py-6 bg-clip-text text-transparent bg-gradient-to-b from-neutral-800 via-neutral-700 to-neutral-700 dark:from-neutral-800 dark:via-white dark:to-white">
            <Cover>Welcome</Cover> <br></br>Signin to your account
           </h1>
        </div>
        <Fieldset className="space-y-6 rounded-xl bg-white/5 p-6 sm:p-10">
          <Field>
            <Label className="text-sm/6 font-medium text-white">Email</Label>
            <Input required type='email'
              className={clsx(
                'mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white',
                'focus:not-data-focus:outline-none data-focus:outline-2 data-focus:-outline-offset-2 data-focus:outline-white/25'
              )}
            />
          </Field>
          <Field>
            <Label className="text-sm/6 font-medium text-white">Password</Label>
            <Input required type='password'
              className={clsx(
                'mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white',
                'focus:not-data-focus:outline-none data-focus:outline-2 data-focus:-outline-offset-2 data-focus:outline-white/25'
              )}
            />
          </Field>
          <div className="flex justify-center">
            <Button className="inline-flex items-center gap-2 rounded-md bg-gray-700 px-3 py-1.5 text-sm/6 font-semibold text-white shadow-inner shadow-white/10 focus:not-data-focus:outline-none data-focus:outline data-focus:outline-white data-hover:bg-gray-600 data-open:bg-gray-700">
              Signup
            </Button>
          </div>
          <div className="text-center text-sm text-neutral-400 pt-4">
            Don't have an account?{' '}
            <a href="#" onClick={(e) => {e.preventDefault();
              onNavigate('signup');
            }}className="font-semibold text-white hover:underline">
              Signup instead
            </a>
          </div>
          
        </Fieldset>
      </div>
      <BackgroundBeams />
    </div>
  );
}

export default function App() {
  const [Page, setPage] = useState('signup');

  interface PageType {
    page: 'signup' | 'login'
  }

  type NavigateHandler = (newPage: PageType['page']) => void;

  const handleNavigate: NavigateHandler = (newPage) => {
    setPage(newPage);
  }

  return (
    <>
     {Page === 'signup' && <SignUpPage onNavigate={handleNavigate}/>}
     {Page === 'login' && <LoginPage onNavigate={handleNavigate}/>}
    </>
  )
}