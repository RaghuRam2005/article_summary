"use client"
import {Field, Fieldset, Input, Label, Button } from '@headlessui/react'
import clsx from 'clsx'
import { Cover } from './components/cover';
import { BackgroundBeams } from './components/background';
import React, { useState, useEffect } from 'react';
import { createUserWithEmailAndPassword, signInWithEmailAndPassword, updateProfile, User } from 'firebase/auth';
import { X, Loader2, User as UserIcon} from 'lucide-react';
import { auth } from '@/firebase/config';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react'



function SignUpPage({ onNavigate }: { onNavigate: (page: 'signup' | 'login' | 'home') => void }) {
  const [displayName, setName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [userPass, setUserPass] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      const userCredentials = await createUserWithEmailAndPassword(auth, userEmail, userPass);
      await updateProfile(userCredentials.user, {displayName})
      onNavigate('home')
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('An Error occured in firebase');
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gray-900">
      <div className='absolute top-4 right-4 z-50'>
        <button onClick={() => onNavigate('home')}
          className="p-2 rounded-full bg-gray-800 text-white hover:bg-gray-700 cursor-pointer">
          <X className='h-6 w-6'/>
        </button>
      </div>
      <div className="w-full max-w-md px-4 relative z-10">
        <div>
          <h1 className="text-4xl md:text-4xl lg:text-6xl font-semibold max-w-7xl mx-auto text-center mt-6 relative z-20 py-6 bg-clip-text text-transparent bg-gradient-to-b from-neutral-800 via-neutral-700 to-neutral-700 dark:from-neutral-800 dark:via-white dark:to-white">
            SignUp to get <br /> <Cover>Started</Cover>
          </h1>
        </div>
        <Fieldset className="space-y-6 rounded-xl bg-gray-950 p-6 sm:p-10">
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
          {error && <p className='text-red-500 text-sm text-center'>{error}</p>}
          <div className="flex justify-center">
            <Button onClick={handleSignup} className="inline-flex items-center gap-2 rounded-md bg-gray-700 px-3 py-1.5 text-sm/6 font-semibold text-white shadow-inner shadow-white/10 focus:not-data-focus:outline-none data-focus:outline data-focus:outline-white data-hover:bg-gray-600 data-open:bg-gray-700 cursor-pointer">
            {isLoading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Please wait...</> : 'Signup'}
            </Button>
          </div>
          <div className="text-center text-sm text-neutral-400 pt-4">
            Already have an account?{' '}
            <a href="" onClick={(e) => {
              e.preventDefault()
              onNavigate('login')
            }} className="font-semibold text-white hover:underline">
              Login instead
            </a>
          </div>
          
        </Fieldset>
      </div>
      <BackgroundBeams />
    </div>
  );
}

function LoginPage({ onNavigate }:{ onNavigate: (page: 'signup' | 'login' | 'home') => void }) {
  const [userEmail, setUserEmail] = useState('');
  const [userPass, setUserPass] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e:React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      const userCredentials = await signInWithEmailAndPassword(auth, userEmail, userPass);
      //onLogin(userCredentials.user)
      onNavigate('home')
    } catch (err:unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('An error occured while logging in')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gray-900">
      <div className='absolute top-4 right-4 z-50'>
        <button onClick={() => onNavigate('home')}
          className="p-2 rounded-full bg-gray-800 text-white hover:bg-gray-700 cursor-pointer">
          <X className='h-6 w-6'/>
        </button>
      </div>
      <div className="w-full max-w-md px-4 relative z-10">
        <div>
          <h1 className="text-4xl md:text-4xl lg:text-6xl font-semibold max-w-7xl mx-auto text-center mt-6 relative z-20 py-6 bg-clip-text text-transparent bg-gradient-to-b from-neutral-800 via-neutral-700 to-neutral-700 dark:from-neutral-800 dark:via-white dark:to-white">
            <Cover>Welcome</Cover> <br></br>Signin to your account
           </h1>
        </div>
        <Fieldset className="space-y-6 rounded-xl bg-gray-950 p-6 sm:p-10">
          <Field>
            <Label className="text-sm/6 font-medium text-white">Email</Label>
            <Input required type='email' placeholder='Enter your email' value={userEmail} onChange={e => setUserEmail(e.target.value)}
              className={clsx(
                'mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white',
                'focus:not-data-focus:outline-none data-focus:outline-2 data-focus:-outline-offset-2 data-focus:outline-white/25'
              )}
            />
          </Field>
          <Field>
            <Label className="text-sm/6 font-medium text-white">Password</Label>
            <Input required type='password' placeholder='Enter your passowrd' value={userPass} onChange={e => setUserPass(e.target.value)}
              className={clsx(
                'mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white',
                'focus:not-data-focus:outline-none data-focus:outline-2 data-focus:-outline-offset-2 data-focus:outline-white/25'
              )}
            />
          </Field>
          {error && <p className='text-red-500 text-sm text-center'>{error}</p>}
          <div className="flex justify-center">
            <Button className="inline-flex items-center gap-2 rounded-md bg-gray-700 px-3 py-1.5 text-sm/6 font-semibold text-white shadow-inner shadow-white/10 focus:not-data-focus:outline-none data-focus:outline data-focus:outline-white data-hover:bg-gray-600 data-open:bg-gray-700 cursor-pointer"
            onClick={handleLogin}>
              {isLoading ? <><Loader2 className='mr-2 h-4 w-4 animate-spin'/>Please wait</> : 'Login'}
            </Button>
          </div>
          <div className="text-center text-sm text-neutral-400 pt-4">
            Don't have an account?{' '}
            <a href="#" onClick={(e) => {e.preventDefault()
              onNavigate('signup')
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

interface HistoryItem {
  id: string;
  query: string;
  type: 'keyword' | 'url' | 'content';
  timestamp: Date;
  response?: string;
}

interface UserProfile {
  displayName: string;
  userEmail: string;
}

type Tab = {
  id: string;
  title: string;
  color: string;
  content: React.ReactNode;
};

const tabs: Tab[] = [
  {
    id: "tab1",
    title: "One",
    color: "#FF0055",
    content: <div>Tab One Content</div>,
  },
  {
    id: "tab2",
    title: "Two",
    color: "#0099FF",
    content: <div>Tab Two Content</div>,
  },
  {
    id: "tab3",
    title: "Three",
    color: "#22CC88",
    content: <div>Tab Three Content</div>,
  },
];

const categories = [
  {
    name: 'Recent',
    posts: [
      {
        id: 1,
        title: 'Does drinking coffee make you smarter?',
        date: '5h ago',
        commentCount: 5,
        shareCount: 2,
      },
      {
        id: 2,
        title: "So you've bought coffee... now what?",
        date: '2h ago',
        commentCount: 3,
        shareCount: 2,
      },
    ],
  },
  {
    name: 'Popular',
    posts: [
      {
        id: 1,
        title: 'Is tech making coffee better or worse?',
        date: 'Jan 7',
        commentCount: 29,
        shareCount: 16,
      },
      {
        id: 2,
        title: 'The most innovative things happening in coffee',
        date: 'Mar 19',
        commentCount: 24,
        shareCount: 12,
      },
    ],
  },
  {
    name: 'Trending',
    posts: [
      {
        id: 1,
        title: 'Ask Me Anything: 10 answers to your questions about coffee',
        date: '2d ago',
        commentCount: 9,
        shareCount: 5,
      },
      {
        id: 2,
        title: "The worst advice we've ever heard about coffee",
        date: '4d ago',
        commentCount: 1,
        shareCount: 2,
      },
    ],
  },
]

function Example() {
  return (
    <div className="flex h-screen w-full justify-center px-4 pt-24">
      <div className="w-full max-w-md">
        <TabGroup>
          <TabList className="flex gap-4">
            {categories.map(({ name }) => (
              <Tab
                key={name}
                className="rounded-full px-3 py-1 text-sm/6 font-semibold text-white focus:not-data-focus:outline-none data-focus:outline data-focus:outline-white data-hover:bg-white/5 data-selected:bg-white/10 data-selected:data-hover:bg-white/10"
              >
                {name}
              </Tab>
            ))}
          </TabList>
          <TabPanels className="mt-3">
            {categories.map(({ name, posts }) => (
              <TabPanel key={name} className="rounded-xl bg-white/5 p-3">
                <ul>
                  {posts.map((post) => (
                    <li key={post.id} className="relative rounded-md p-3 text-sm/6 transition hover:bg-white/5">
                      <a href="#" className="font-semibold text-white">
                        <span className="absolute inset-0" />
                        {post.title}
                      </a>
                      <ul className="flex gap-2 text-white/50" aria-hidden="true">
                        <li>{post.date}</li>
                        <li aria-hidden="true">&middot;</li>
                        <li>{post.commentCount} comments</li>
                        <li aria-hidden="true">&middot;</li>
                        <li>{post.shareCount} shares</li>
                      </ul>
                    </li>
                  ))}
                </ul>
              </TabPanel>
            ))}
          </TabPanels>
        </TabGroup>
      </div>
    </div>
  )
}

export default function App() {
  const [Page, setPage] = useState('home');

  interface PageType {
    page: 'signup' | 'login' | 'home';
  }

  type NavigateHandler = (newPage: PageType['page']) => void;

  const handleNavigate: NavigateHandler = (newPage) => {
    setPage(newPage);
  }
  
  return (
    <>
      {Page === 'signup' && <SignUpPage onNavigate={handleNavigate}/>}
      {Page === 'login' && <LoginPage onNavigate={handleNavigate}/>}
      {Page === 'home' && <Example onNavigate={handleNavigate}/>}
    </>
  )
}