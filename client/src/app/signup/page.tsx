"use client";

import { Button } from "../../components/ui/button";
import { IconBrandGoogle } from "@tabler/icons-react";
import { signIn, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useIsDarkMode } from "@/hooks/useDarkMode";
import { useEffect, useState } from "react";

export default function Signup() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const isDarkModeHook = useIsDarkMode();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);
  useEffect(() => {
    if (status === "authenticated") {
      router.push("/layout");
    }
  }, [status, router]);

  const isLoading = status === "loading";
  const isDarkMode = mounted ? isDarkModeHook : false;

  const handleGoogleSignIn = async () => {
    try {
      await signIn("google", {
        callbackUrl: "/layout",
      });
    } catch (error) {
      console.error("Sign in error:", error);
    }
  };

  if (isLoading || !mounted) {
    return (
      <div
        className={`flex h-screen items-center justify-center ${
          isDarkMode ? "bg-gray-900 text-white" : "bg-black text-white"
        }`}
      >
        Loading...
      </div>
    );
  }

  return (
    <div
      className={`min-h-screen flex ${isDarkMode ? "bg-gray-900" : "bg-black"}`}
    >
      <div className="flex-1 flex flex-col justify-center items-center px-8 lg:px-16">
        <div className="max-w-md w-full space-y-16">
          <div className="text-center">
            <h1 className={`text-4xl lg:text-6xl font-bold mb-8 text-white`}>
              Impossible?
            </h1>
            <h1 className={`text-4xl lg:text-6xl font-bold mb-14 text-white`}>
              Possible.
            </h1>
            <p className={`text-3xl mb-16 text-white`}>Slides Generator</p>
          </div>

          <div className="space-y-4">
            <Button
              variant="outline"
              size="lg"
              className={`w-full ${
                isDarkMode ? "border-gray-400 text-gray-200" : "border-white"
              }`}
              onClick={handleGoogleSignIn}
              disabled={isLoading}
            >
              <IconBrandGoogle stroke={2} />
              {isLoading ? "Loading..." : "Continue with Google"}
            </Button>
          </div>
        </div>
      </div>

      <div className="hidden lg:flex flex-1 items-center justify-center p-8">
        <div
          className={`w-full h-full max-w-lg max-h-96 rounded-2xl flex items-center justify-center ${
            isDarkMode
              ? "bg-gradient-to-br from-gray-700 to-gray-900"
              : "bg-gradient-to-br from-orange-400 to-red-500"
          }`}
        >
          <div
            className={`text-center ${
              isDarkMode ? "text-gray-200" : "text-white"
            }`}
          >
            <div className="text-6xl mb-4">🎨</div>
            <p className="text-lg">Your image here</p>
          </div>
        </div>
      </div>
    </div>
  );
}
