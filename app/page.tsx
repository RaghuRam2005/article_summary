"use client";
import { Field, Fieldset, Input, Label, Button, Textarea, Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';
import clsx from 'clsx';
import { Cover } from '@/app/components/cover';
import { BackgroundBeams } from '@/app/components/background';
import React, { useState, useEffect, Fragment } from 'react';
import { createUserWithEmailAndPassword, signInWithEmailAndPassword, updateProfile, onAuthStateChanged, signOut, User, updateEmail, updatePassword, reauthenticateWithCredential, EmailAuthProvider } from 'firebase/auth';
import { auth, db } from '@/app/firebase/config';
import { collection, addDoc, query, onSnapshot, deleteDoc, doc, orderBy } from 'firebase/firestore';
import { X, Loader2, User as UserIcon, LogOut, Trash2, Send, History, KeyRound, Mail, Menu, SidebarClose } from 'lucide-react';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';

// Backend url
const BackendUrl = "http://127.0.0.1:5000/"

// --- AUTH PAGES ---

function SignUpPage({ onNavigate }: { onNavigate: (page: 'signup' | 'login' | 'home') => void }) {
  const [displayName, setName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [userPass, setUserPass] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const userCredentials = await createUserWithEmailAndPassword(auth, userEmail, userPass);
      await updateProfile(userCredentials.user, { displayName });
      onNavigate('home');
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An Error occurred in firebase');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gray-900 text-white">
      <div className='absolute top-4 right-4 z-50'>
        <button onClick={() => onNavigate('home')} className="p-2 rounded-full bg-gray-800 hover:bg-gray-700 cursor-pointer">
          <X className='h-6 w-6'/>
        </button>
      </div>
      <div className="w-full max-w-md px-4 relative z-10">
        <h1 className="text-4xl md:text-5xl font-semibold text-center mt-6 relative z-20 py-6 bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 to-neutral-500">
          Sign Up to Get <Cover>Started</Cover>
        </h1>
        <Fieldset className="space-y-6 rounded-xl bg-black/50 p-6 sm:p-10 border border-gray-700">
          <Field>
            <Label className="text-sm/6 font-medium text-gray-300">Name</Label>
            <Input required type='text' placeholder='Enter your name' value={displayName} onChange={e => setName(e.target.value)}
              className={clsx('mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white', 'focus:outline-none data-[focus]:outline-2 data-[focus]:-outline-offset-2 data-[focus]:outline-white/25')}
            />
          </Field>
          <Field>
            <Label className="text-sm/6 font-medium text-gray-300">Email</Label>
            <Input required type='email' placeholder='Enter your email' value={userEmail} onChange={e => setUserEmail(e.target.value)}
              className={clsx('mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white', 'focus:outline-none data-[focus]:outline-2 data-[focus]:-outline-offset-2 data-[focus]:outline-white/25')}
            />
          </Field>
          <Field>
            <Label className="text-sm/6 font-medium text-gray-300">Password</Label>
            <Input required type='password' placeholder='Enter your password' value={userPass} onChange={e => setUserPass(e.target.value)}
              className={clsx('mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white', 'focus:outline-none data-[focus]:outline-2 data-[focus]:-outline-offset-2 data-[focus]:outline-white/25')}
            />
          </Field>
          {error && <p className='text-red-500 text-sm text-center'>{error}</p>}
          <div className="flex justify-center">
            <Button onClick={handleSignup} className="inline-flex items-center gap-2 rounded-md bg-gray-700 px-4 py-2 text-sm/6 font-semibold text-white shadow-inner shadow-white/10 hover:bg-gray-600 data-[focus]:outline-1 data-[focus]:outline-white">
              {isLoading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Please wait...</> : 'Sign Up'}
            </Button>
          </div>
          <div className="text-center text-sm text-neutral-400 pt-4">
            Already have an account?{' '}
            <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('login'); }} className="font-semibold text-white hover:underline">
              Login
            </a>
          </div>
        </Fieldset>
      </div>
      <BackgroundBeams />
    </div>
  );
}

function LoginPage({ onNavigate }: { onNavigate: (page: 'signup' | 'login' | 'home') => void }) {
  const [userEmail, setUserEmail] = useState('');
  const [userPass, setUserPass] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await signInWithEmailAndPassword(auth, userEmail, userPass);
      onNavigate('home');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An error occurred while logging in');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gray-900 text-white">
       <div className='absolute top-4 right-4 z-50'>
        <button onClick={() => onNavigate('home')} className="p-2 rounded-full bg-gray-800 hover:bg-gray-700 cursor-pointer">
          <X className='h-6 w-6'/>
        </button>
      </div>
      <div className="w-full max-w-md px-4 relative z-10">
        <h1 className="text-4xl md:text-5xl font-semibold text-center mt-6 relative z-20 py-6 bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 to-neutral-500">
          <Cover>Welcome Back</Cover>
        </h1>
        <Fieldset className="space-y-6 rounded-xl bg-black/50 p-6 sm:p-10 border border-gray-700">
          <Field>
            <Label className="text-sm/6 font-medium text-gray-300">Email</Label>
            <Input required type='email' placeholder='Enter your email' value={userEmail} onChange={e => setUserEmail(e.target.value)}
              className={clsx('mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white', 'focus:outline-none data-[focus]:outline-2 data-[focus]:-outline-offset-2 data-[focus]:outline-white/25')}
            />
          </Field>
          <Field>
            <Label className="text-sm/6 font-medium text-gray-300">Password</Label>
            <Input required type='password' placeholder='Enter your password' value={userPass} onChange={e => setUserPass(e.target.value)}
              className={clsx('mt-3 block w-full rounded-lg border-none bg-gray-800 px-3 py-1.5 text-sm/6 text-white', 'focus:outline-none data-[focus]:outline-2 data-[focus]:-outline-offset-2 data-[focus]:outline-white/25')}
            />
          </Field>
          {error && <p className='text-red-500 text-sm text-center'>{error}</p>}
          <div className="flex justify-center">
            <Button onClick={handleLogin} className="inline-flex items-center gap-2 rounded-md bg-gray-700 px-4 py-2 text-sm/6 font-semibold text-white shadow-inner shadow-white/10 hover:bg-gray-600 data-[focus]:outline-1 data-[focus]:outline-white">
              {isLoading ? <><Loader2 className='mr-2 h-4 w-4 animate-spin'/>Please wait</> : 'Login'}
            </Button>
          </div>
          <div className="text-center text-sm text-neutral-400 pt-4">
            Don't have an account?{' '}
            <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('signup'); }} className="font-semibold text-white hover:underline">
              Sign Up
            </a>
          </div>
        </Fieldset>
      </div>
      <BackgroundBeams />
    </div>
  );
}

// --- MAIN APP COMPONENTS ---

interface HistoryItem {
  id: string;
  query: string;
  type: 'keyword' | 'url' | 'content';
  timestamp: any;
  response: string;
}

function ProfileModal({ isOpen, setIsOpen, user }: { isOpen: boolean, setIsOpen: (isOpen: boolean) => void, user: User }) {
  const [displayName, setDisplayName] = useState(user.displayName || '');
  const [newEmail, setNewEmail] = useState(user.email || '');
  const [newPassword, setNewPassword] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleUpdate = async (updateType: 'profile' | 'email' | 'password') => {
    setError('');
    setSuccess('');
    setIsLoading(true);

    if (!user) {
        setError("No user is signed in.");
        setIsLoading(false);
        return;
    }

    try {
        const credential = EmailAuthProvider.credential(user.email!, currentPassword);
        await reauthenticateWithCredential(user, credential);

        if (updateType === 'profile') {
            await updateProfile(user, { displayName });
            setSuccess("Display name updated successfully!");
        } else if (updateType === 'email') {
            await updateEmail(user, newEmail);
            setSuccess("Email updated successfully!");
        } else if (updateType === 'password') {
            await updatePassword(user, newPassword);
            setSuccess("Password updated successfully!");
            setNewPassword('');
        }
    } catch (err) {
        if (err instanceof Error) {
            setError(err.message);
        } else {
            setError("An unknown error occurred.");
        }
    } finally {
        setIsLoading(false);
        setCurrentPassword('');
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={() => setIsOpen(false)}>
        <TransitionChild as={Fragment} enter="ease-out duration-300" enterFrom="opacity-0" enterTo="opacity-100" leave="ease-in duration-200" leaveFrom="opacity-100" leaveTo="opacity-0">
          <div className="fixed inset-0 bg-black/50" />
        </TransitionChild>
        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <TransitionChild as={Fragment} enter="ease-out duration-300" enterFrom="opacity-0 scale-95" enterTo="opacity-100 scale-100" leave="ease-in duration-200" leaveFrom="opacity-100 scale-100" leaveTo="opacity-0 scale-95">
              <DialogPanel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-gray-900 p-6 text-left align-middle shadow-xl transition-all border border-gray-700 text-white">
                <DialogTitle as="h3" className="text-lg font-medium leading-6 text-white flex justify-between items-center">
                  Profile Settings
                  <button onClick={() => setIsOpen(false)} className="p-1 rounded-full hover:bg-gray-700"><X size={20}/></button>
                </DialogTitle>
                <div className="mt-4 space-y-6">
                  {error && <p className='text-red-500 text-sm text-center'>{error}</p>}
                  {success && <p className='text-green-500 text-sm text-center'>{success}</p>}
                  
                  {/* Display Name */}
                  <Fieldset className="space-y-2">
                      <Label className="text-sm/6 font-medium text-gray-300">Display Name</Label>
                      <div className="flex gap-2">
                          <Input value={displayName} onChange={e => setDisplayName(e.target.value)} className="flex-grow rounded-md bg-gray-800 px-3 py-1.5 text-sm/6" />
                          <Button onClick={() => handleUpdate('profile')} disabled={isLoading} className="px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-sm font-semibold disabled:bg-gray-500">
                            {isLoading ? <Loader2 className="animate-spin" /> : "Save"}
                          </Button>
                      </div>
                  </Fieldset>

                  {/* Email & Password */}
                  <div className="border-t border-gray-700 pt-6 space-y-4">
                      <p className="text-sm text-gray-400">To update your email or password, please enter your current password first.</p>
                      <Field>
                          <Label className="text-sm/6 font-medium text-gray-300">Current Password</Label>
                          <Input type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} placeholder="Enter current password" className="mt-1 block w-full rounded-md bg-gray-800 px-3 py-1.5 text-sm/6" />
                      </Field>
                      
                      <Fieldset className="space-y-2" disabled={!currentPassword}>
                          <Label className="text-sm/6 font-medium text-gray-300">New Email</Label>
                          <div className="flex gap-2">
                              <Input type="email" value={newEmail} onChange={e => setNewEmail(e.target.value)} className="flex-grow rounded-md bg-gray-800 px-3 py-1.5 text-sm/6" />
                              <Button onClick={() => handleUpdate('email')} disabled={isLoading || !currentPassword} className="px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-sm font-semibold disabled:bg-gray-500">
                                {isLoading ? <Loader2 className="animate-spin" /> : "Update"}
                              </Button>
                          </div>
                      </Fieldset>

                      <Fieldset className="space-y-2" disabled={!currentPassword}>
                          <Label className="text-sm/6 font-medium text-gray-300">New Password</Label>
                          <div className="flex gap-2">
                              <Input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="Enter new password" className="flex-grow rounded-md bg-gray-800 px-3 py-1.5 text-sm/6" />
                              <Button onClick={() => handleUpdate('password')} disabled={isLoading || !currentPassword} className="px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-sm font-semibold disabled:bg-gray-500">
                                {isLoading ? <Loader2 className="animate-spin" /> : "Update"}
                              </Button>
                          </div>
                      </Fieldset>
                  </div>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}


function Sidebar({ user, onHistorySelect, onLogout, onNavigate }: { user: User, onHistorySelect: (item: HistoryItem) => void, onLogout: () => void, onNavigate: (page: 'signup' | 'login' | 'home') => void }) {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  useEffect(() => {
    if (user) {
      const q = query(collection(db, 'history', user.uid, 'queries'), orderBy('timestamp', 'desc'));
      const unsubscribe = onSnapshot(q, (querySnapshot) => {
        const historyData: HistoryItem[] = [];
        querySnapshot.forEach((doc) => {
          historyData.push({ id: doc.id, ...doc.data() } as HistoryItem);
        });
        setHistory(historyData);
      });
      return () => unsubscribe();
    }
  }, [user]);

  const handleDelete = async (id: string) => {
    if (user) {
      await deleteDoc(doc(db, 'history', user.uid, 'queries', id));
    }
  };

  return (
    <>
      <div className="h-full bg-gray-900/70 backdrop-blur-md text-white flex flex-col border-r border-gray-700">
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-xl font-semibold flex items-center gap-2"><History size={24}/> History</h2>
        </div>
        <div className="flex-grow overflow-y-auto">
          {history.map(item => (
            <div key={item.id} className="p-3 hover:bg-gray-800/50 group flex justify-between items-center cursor-pointer" onClick={() => onHistorySelect(item)}>
              <p className="truncate text-sm">{item.query}</p>
              <button onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }} className="text-gray-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
        <div className="p-4 border-t border-gray-700 space-y-2">
          <Button onClick={() => setIsProfileOpen(true)} className="w-full flex items-center gap-2 justify-center rounded-md bg-gray-700 px-3 py-2 text-sm/6 font-semibold shadow-inner shadow-white/10 hover:bg-gray-600">
            <UserIcon size={16} /> {user.displayName || 'Profile'}
          </Button>
          <Button onClick={onLogout} className="w-full flex items-center gap-2 justify-center rounded-md bg-red-800/80 px-3 py-2 text-sm/6 font-semibold shadow-inner shadow-white/10 hover:bg-red-700">
            <LogOut size={16} /> Logout
          </Button>
        </div>
      </div>
      {user && <ProfileModal isOpen={isProfileOpen} setIsOpen={setIsProfileOpen} user={user} />}
    </>
  );
}

function MainContent({ user, activeResult, setActiveResult }: { user: User, activeResult: HistoryItem | null, setActiveResult: (result: HistoryItem | null) => void }) {
  const [inputType, setInputType] = useState(0);
  const [keyword, setKeyword] = useState('');
  const [url, setUrl] = useState('');
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSummarize = async () => {
    let query = '';
    let type: 'keyword' | 'url' | 'content' = 'keyword';

    if (inputType === 0) { query = keyword; type = 'keyword'; }
    else if (inputType === 1) { query = url; type = 'url'; }
    else { query = content; type = 'content'; }

    if (!query.trim()) return;

    setIsLoading(true);

    // Prepare request payload
    const payload: Record<string, string> = {};
    if (type === 'keyword') payload.keyword = query;
    else if (type === 'url') payload.url = query;
    else payload.content = query;

    let summary = '';
    try {
      const res = await fetch(`${BackendUrl}/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.status === 'success' && data.summary) {
      summary = data.summary;
      } else {
      summary = 'Failed to generate summary.';
      }
    } catch (err) {
      summary = 'Error connecting to backend.';
    }

    const newHistoryItem = {
      query,
      type,
      response: summary,
      timestamp: new Date(),
    };

    if (user) {
      await addDoc(collection(db, 'history', user.uid, 'queries'), newHistoryItem);
    }
    
    setActiveResult({ id: 'new', ...newHistoryItem });
    setIsLoading(false);
    setKeyword('');
    setUrl('');
    setContent('');
  };

  const inputTabs = [
    { name: 'Keyword', content: <Input value={keyword} onChange={e => setKeyword(e.target.value)} placeholder="Enter a keyword or topic" className="w-full bg-gray-800 rounded-md p-3 text-white border border-gray-700 focus:ring-2 focus:ring-blue-500 focus:outline-none" /> },
    { name: 'URL', content: <Input value={url} onChange={e => setUrl(e.target.value)} placeholder="https://example.com" className="w-full bg-gray-800 rounded-md p-3 text-white border border-gray-700 focus:ring-2 focus:ring-blue-500 focus:outline-none" /> },
    { name: 'Content', content: <Textarea value={content} onChange={e => setContent(e.target.value)} placeholder="Paste your text here..." className="w-full bg-gray-800 rounded-md p-3 text-white border border-gray-700 h-48 resize-none focus:ring-2 focus:ring-blue-500 focus:outline-none" /> },
  ];

  if (activeResult) {
    return (
      <div className="p-6 md:p-10 h-full overflow-y-auto">
        <Button onClick={() => setActiveResult(null)} className="mb-6 inline-flex items-center gap-2 rounded-md bg-gray-700 px-3 py-1.5 text-sm/6 font-semibold text-white shadow-inner shadow-white/10 hover:bg-gray-600">
          New Summary
        </Button>
        <div className="space-y-6">
          <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
            <h3 className="font-semibold text-lg text-gray-300 mb-2">Your Query ({activeResult.type})</h3>
            <p className="text-gray-400 whitespace-pre-wrap break-words">{activeResult.query}</p>
          </div>
          <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
            <h3 className="font-semibold text-lg text-blue-400 mb-2">Generated Summary</h3>
            <p className="text-gray-200 whitespace-pre-wrap break-words">{activeResult.response}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full p-6 md:p-10 justify-center">
      <div className="w-full max-w-2xl mx-auto">
        <h1 className="text-3xl md:text-4xl font-bold text-center mb-8 bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 to-neutral-600">
          Summarize Anything
        </h1>
        <TabGroup selectedIndex={inputType} onChange={setInputType}>
          <TabList className="flex gap-4 justify-center">
            {inputTabs.map((tab) => (
              <Tab key={tab.name} className="rounded-full px-4 py-2 text-sm/6 font-semibold text-white focus:outline-none data-[focus]:outline-1 data-[focus]:outline-white data-[hover]:bg-white/10 data-[selected]:bg-white/15 data-[selected]:data-[hover]:bg-white/15 transition-colors">
                {tab.name}
              </Tab>
            ))}
          </TabList>
          <TabPanels className="mt-6">
            {inputTabs.map((tab) => (
              <TabPanel key={tab.name}>
                {tab.content}
              </TabPanel>
            ))}
          </TabPanels>
        </TabGroup>
        <div className="mt-8 flex justify-center">
          <Button onClick={handleSummarize} disabled={isLoading} className="inline-flex items-center gap-3 rounded-full bg-blue-600 px-8 py-3 text-lg font-semibold text-white shadow-lg hover:bg-blue-500 transition-all transform hover:scale-105 disabled:bg-gray-500 disabled:scale-100">
            {isLoading ? <><Loader2 className="h-5 w-5 animate-spin" /> Processing...</> : <><Send size={20}/> Summarize</>}
          </Button>
        </div>
      </div>
    </div>
  );
}

function HomePage({ user, onLogout, onNavigate }: { user: User, onLogout: () => void, onNavigate: (page: 'signup' | 'login' | 'home') => void }) {
  const [activeResult, setActiveResult] = useState<HistoryItem | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const handleHistorySelect = (item: HistoryItem) => {
    setActiveResult(item);
    if(window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  };

  return (
    <div className="h-screen w-screen bg-gray-950 text-white flex">
      <div className={clsx("fixed md:relative z-40 h-full w-64 md:w-72 lg:w-80 transition-transform transform", {
        "translate-x-0": isSidebarOpen,
        "-translate-x-full md:translate-x-0": !isSidebarOpen,
      })}>
        <Sidebar user={user} onHistorySelect={handleHistorySelect} onLogout={onLogout} onNavigate={onNavigate} />
      </div>
      
      <main className="flex-1 flex flex-col relative">
        <div className="absolute top-4 left-4 md:hidden z-50">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 bg-gray-800/50 rounded-md">
            {isSidebarOpen ? <SidebarClose /> : <Menu />}
          </button>
        </div>
        <div className="flex-1 relative">
            <MainContent user={user} activeResult={activeResult} setActiveResult={setActiveResult} />
            <BackgroundBeams className="z-[-1]"/>
        </div>
      </main>
    </div>
  );
}

// --- APP ENTRY POINT ---

export default function App() {
  const [page, setPage] = useState<'signup' | 'login' | 'home'>('home');
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setIsLoading(false);
    });
    return () => unsubscribe();
  }, []);

  const handleNavigate = (newPage: 'signup' | 'login' | 'home') => {
    setPage(newPage);
  };

  const handleLogout = async () => {
    await signOut(auth);
    setPage('home'); // or 'login'
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen w-full items-center justify-center bg-gray-900 text-white">
        <Loader2 className="h-12 w-12 animate-spin text-blue-500" />
      </div>
    );
  }

  if (user) {
    return <HomePage user={user} onLogout={handleLogout} onNavigate={handleNavigate} />;
  }

  if (page === 'signup') {
    return <SignUpPage onNavigate={handleNavigate} />;
  }
  
  if (page === 'login') {
    return <LoginPage onNavigate={handleNavigate} />;
  }

  // Default landing page for non-logged-in users
  return (
     <div className="flex flex-col min-h-screen w-full items-center justify-center bg-gray-900 text-white p-4">
        <div className="absolute top-4 right-4 z-10 flex gap-2">
            <Button onClick={() => handleNavigate('login')} className="rounded-md bg-gray-700 px-4 py-2 text-sm/6 font-semibold shadow-inner shadow-white/10 hover:bg-gray-600">Login</Button>
            <Button onClick={() => handleNavigate('signup')} className="rounded-md bg-blue-600 px-4 py-2 text-sm/6 font-semibold shadow-lg hover:bg-blue-500">Sign Up</Button>
        </div>
        <div className="text-center relative z-10">
            <h1 className="text-5xl md:text-7xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-neutral-50 to-neutral-400 py-4">
                AI <Cover>Summarizer</Cover>
            </h1>
            <p className="mt-4 text-lg text-neutral-300 max-w-2xl mx-auto">
                Effortlessly condense articles, documents, and web pages into concise summaries. Log in to save your history and access your work from anywhere.
            </p>
        </div>
       <BackgroundBeams />
    </div>
  );
}
