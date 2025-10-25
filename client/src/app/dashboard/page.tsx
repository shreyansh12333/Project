"use client";

import { useSession, signOut } from "next-auth/react";
import { Button } from "../../components/ui/button";
import { useRouter } from "next/navigation";

export default function Dashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  if (!session) {
    router.push("/signup");
    return null;
  }

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-8">
      <div className="max-w-md w-full space-y-8 text-center">
        <div>
          <h1 className="text-4xl font-bold text-white mb-4">
            Welcome to Dashboard! 🎉
          </h1>
          <div className="text-white space-y-2">
            <p>Hello, {session.user?.name}!</p>
            <p>Email: {session.user?.email}</p>
            {session.user?.image && (
              <img 
                src={session.user.image} 
                alt="Profile" 
                className="w-16 h-16 rounded-full mx-auto mt-4"
              />
            )}
          </div>
        </div>
        
        <Button 
          variant="outline" 
          onClick={() => signOut({ callbackUrl: "/signup" })}
          className="w-full"
        >
          Sign Out
        </Button>
      </div>
    </div>
  );
}
