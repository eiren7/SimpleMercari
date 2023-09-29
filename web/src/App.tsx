import { useState } from "react"
import "./App.css"
import "./MediaQuery.css"
import { ItemList } from "./components/ItemList"
import { Listing } from "./components/Listing"

function App() {
  // reload ItemList after Listing complete
  const [reload, setReload] = useState(true)
  return (
    <div>
      <div>
        <Listing onListingCompleted={() => setReload(true)} />
      </div>
      <div>
        <ItemList reload={reload} onLoadCompleted={() => setReload(false)} />
      </div>
    </div>
  )
}

export default App